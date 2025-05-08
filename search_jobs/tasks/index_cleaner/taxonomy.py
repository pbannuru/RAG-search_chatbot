import pandas as pd
from batch_jobs.internal.scheduler.task import Task
from batch_jobs.tasks.utils.utils import *


class Taxonomy(Task):

    def __init__(self):
        self.indigo_unique_dict = {}
        self.pwp_unique_dict = {}
        super().__init__("taxonomy_updation_task")

    def run(self):
        super().run()
        self.updating_files()

    def fetch_data_recursive(self, product_id):
        products = {}  # Initialize products inside the function
        access_token = kaas_access_token()
        url = app_configs["kaas_api_base_url"]
        # url = 'https://css.api.hp.com/knowledge/v2/search'
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        def recursive_fetch(product_id):
            params = {
                "resultLimit": "10",
                "store": "tmsstore",
                "filters": f"productid:{product_id}",
                "printFields": "title,tmspmnamevalue,tmspmnumbervalue,tmspmseriesvalue,tmsnodedepth,childnodes,description",
            }

            # Make the API request
            response = requests.get(url, params=params, headers=headers)
            data = response.json()

            # Check if data is valid
            if not data or "matches" not in data or not data["matches"]:
                return  # Continue to the next child without stopping the function

            # Store data for the current node
            product_data = data["matches"][0]
            products[product_id] = {
                "name": product_data.get("name", "Unknown"),
                "tmsNodeDepth": product_data.get("tmsNodeDepth", "Unknown"),
                "childnodes": product_data.get("childnodes", ""),
                "description": product_data.get(
                    "description", "No description available"
                ),
            }

            # Process child nodes if available
            child_nodes = product_data.get("childnodes", "")
            if child_nodes:
                # Split child nodes by '|' and iterate
                for child_id in child_nodes.split("|"):
                    recursive_fetch(child_id)

        # Start recursive fetching
        recursive_fetch(product_id)

        return products

    def taxonomy_preprocessing(self, device_dict):

        df = pd.DataFrame(device_dict).transpose().reset_index()
        df.rename(columns={"index": "id"}, inplace=True)
        df = df.sort_values(by="tmsNodeDepth")
        df["id"] = df["id"].astype(str)
        df["product_name"] = df.apply(
            lambda row: (
                row["name"]
                if row["name"]
                and (
                    row["name"].startswith("HP")
                    or row["name"].lower().endswith(("press", "presses"))
                )
                else (
                    row["description"]
                    if row["description"]
                    and (
                        row["description"].startswith("HP")
                        or row["description"].lower().endswith(("press", "presses"))
                    )
                    else (
                        row["name"]
                        if row["name"] == row["description"]
                        else (
                            row["name"]
                            if row["description"] == ""
                            else row["description"] if row["name"] == "" else None
                        )
                    )
                )
            ),
            axis=1,
        )
        id_to_name = dict(zip(df["id"], df["product_name"]))
        df["childnodes"] = df["childnodes"].apply(lambda x: x.split("|"))
        df["childnode_names"] = df["childnodes"].apply(
            lambda x: (
                {id.strip(): id_to_name.get(id.strip()) for id in x if id.strip()}
                if x
                else {}
            )
        )
        df = df.reset_index(drop=True)
        df.fillna("", inplace=True)
        df["id_name_mapping"] = df.apply(
            lambda row: {
                child_id: row["product_name"]
                for child_id in row["childnodes"]
                if child_id
            },
            axis=1,
        )
        return df

    def new_devices_source(self):
        # obj=Taxonomy()
        pwp = self.fetch_data_recursive(4211033)
        indigo = self.fetch_data_recursive(236258)
        pwp_tdf = self.taxonomy_preprocessing(pwp)
        indigo_tdf = self.taxonomy_preprocessing(indigo)
        # pwp_tdf = pwp_tdf[~pwp_tdf['product_name'].str.contains('C5', case=False, na=False)]
        # indigo_tdf = indigo_tdf[~indigo_tdf['product_name'].str.contains('C5', case=False, na=False)]


        for i in indigo_tdf["id_name_mapping"]:
            for key, value in i.items():  # Unpack each key-value pair individually
                self.indigo_unique_dict[key] = value
        for i in pwp_tdf["id_name_mapping"]:
            for key, value in i.items():  # Unpack each key-value pair individually
                self.pwp_unique_dict[key] = value

        indigo_source_pr = {i for i in self.indigo_unique_dict.keys()}
        pwp_source_pr = {i for i in self.pwp_unique_dict.keys()}
        print(len(indigo_source_pr), len(pwp_source_pr))

        kaas_domain_map_path = app_configs["kaas_domain_map_path"]
        # kaas_file = 'kaas_domain_map.csv'
        f = pd.read_csv(kaas_domain_map_path, dtype={"product_id": str})

        domain_map = dict(zip(f["product_id"], f["domain"]))
        excel_products = pd.DataFrame.from_dict(
            domain_map, orient="index"
        ).reset_index()
        excel_products.columns = ["products", "domain"]

        excel_indigo_pr = set(
            excel_products[excel_products["domain"] == "Indigo"]["products"].to_list()
        )
        excel_pwp_pr = set(
            excel_products[excel_products["domain"] == "PWP"]["products"].to_list()
        )

        pwp_new_datakeys = pwp_source_pr - excel_pwp_pr
        indigo_new_datakeys = indigo_source_pr - excel_indigo_pr

        indigo_new_datakeys = [
            key
            for key in indigo_new_datakeys
            if "C5" not in self.indigo_unique_dict[key]
        ]
        pwp_new_datakeys = [
            key for key in pwp_new_datakeys if "C5" not in self.pwp_unique_dict[key]
        ]
        print(len(indigo_new_datakeys), len(pwp_new_datakeys))
        return indigo_new_datakeys, pwp_new_datakeys

    def updating_files(self):
        indigo_new_datakeys, pwp_new_datakeys = self.new_devices_source()
        if indigo_new_datakeys or pwp_new_datakeys:
            indigo_new_entries = pd.DataFrame(
                {"product_id": list(indigo_new_datakeys), "domain": "Indigo"}
            )

            pwp_new_entries = pd.DataFrame(
                {"product_id": list(pwp_new_datakeys), "domain": "PWP"}
            )
            kaas_domain_map_path = app_configs["kaas_domain_map_path"]
            # kaas_file = 'kaas_domain_map.csv'
            f = pd.read_csv(kaas_domain_map_path, dtype={"product_id": str})
            updated_data = pd.concat(
                [f, indigo_new_entries, pwp_new_entries], ignore_index=True
            )
            updated_data.to_csv("kaas_domain_map.csv", index=False)
            print("updated file kaas_domain_map.csv")

            look_path = app_configs["look_path"]
            f1 = pd.read_csv(look_path)
            # f1=pd.read_csv('lookup.csv')
            f1["id"] = f1["id"].astype(str)

            indigo_new_entries_with_n = pd.DataFrame(
                {
                    "id": list(indigo_new_datakeys),
                    "name": [
                        self.indigo_unique_dict[key] for key in indigo_new_datakeys
                    ],
                }
            )

            pwp_new_entries_with_n = pd.DataFrame(
                {
                    "id": list(pwp_new_datakeys),
                    "name": [self.pwp_unique_dict[key] for key in pwp_new_datakeys],
                }
            )
            updated_data1 = pd.concat(
                [f1, indigo_new_entries_with_n, pwp_new_entries_with_n],
                ignore_index=True,
            )
            updated_data1.to_csv("lookup.csv", index=False)
            print("updated file: lookup.csv")

            path = app_configs["kaas_products"]
            f3 = pd.read_csv(path)
            # f3 = pd.read_csv('kaas_products.csv')
            product_ids = (
                f3["product_id"].astype(str).tolist()
            )  # Convert IDs to strings
            product_ids.extend(list(indigo_new_datakeys))
            product_ids.extend(list(pwp_new_datakeys))
            updated_data2 = pd.DataFrame(product_ids, columns=["product_id"])
            updated_data2.to_csv("kaas_products.csv", index=False)
            print("updated file: kaas_products.csv")
