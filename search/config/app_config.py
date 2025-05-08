import configparser
import os
from app.config.env import environment


class AppConfig:
    # Retrieve config values from configs.ini file
    config = configparser.ConfigParser()
    # Fetch server detail from env.local and use the respective configs.ini file
    conf_file = os.getcwd() + "/config/" + environment.SERVER_ENV.value + "/configs.ini"

    @classmethod
    def get_all_configs(cls):
        """
        Returns a dictionary of all key value config pairs
        for all the defined sections
        """
        cls.config.read(cls.conf_file)
        config_params = {}
        try:
            for sec in cls.config.sections():
                for key, val in cls.config.items(sec):
                    config_params[key] = val
        except (ValueError, KeyError) as e:
            print(
                "Failed to read config file - %s. Reason - %s ", cls.conf_file, str(e)
            )
        return config_params

    @classmethod
    def get_sectionwise_configs(cls, section):
        """
        Returns dictionary of configs defined under given section name
        """
        cls.config.read(cls.conf_file)
        config_params = {}
        try:
            for key, val in cls.config.items(section):
                config_params[key] = val
        except (ValueError, KeyError) as e:
            print("Failed to read config file - %s. Reason - %s", cls.conf_file, str(e))
        return config_params

    @classmethod
    def get_config_value_for_key(cls, section, key):
        """
        Returns the value (str) for the given config key under the given section.
        It returns boolean as String itself. Please use 'eval(config_value)' in code
        wherever You expect a boolean config value.
        """
        cls.config.read(cls.conf_file)
        config_value = ""
        try:
            config_value = cls.config.get(section, key)
        except Exception as e:
            print("Failed to read config file %s . Reason - %s", cls.conf_file, str(e))
        return config_value
    

app_configs = AppConfig.get_all_configs()
