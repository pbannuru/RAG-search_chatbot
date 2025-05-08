# Sample 500 exception format
sample_exception = {
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "message": "Internal Server Error",
                        "log_id": "32c12aed-2178-11ef-ab87-6045bdad83c8",
                    }
                }
            }
        },
    },
}

# Example responses for APIs
response_example_autosuggest = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 9,
                        "limit": 10,
                        "query": "label",
                        "device": "Indigo 7000",
                        "persona": "operator",
                        "domain": "indigo",
                        "source": "kaas",
                    },
                    "data": [
                        "Blanket reuse label N/A N/A",
                        "DOA Red Label Download this label and attach it to a DOA part for return to HP CA396-06890",
                    ],
                }
            }
        },
    },
}
response_example_autosuggest.update(sample_exception)

# Example responses
response_example_search = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 1,
                        "limit": 1,
                        "query": "label",
                        "device": "Indigo 7000",
                        "persona": "operator",
                        "domain": "indigo",
                    },
                    "data": [
                        {
                            "documentID": "4AA6-4534EEE",
                            "score": 0.7,
                            "title": "PrintOS Brochure",
                            "description": "End to end brochure, cross business units, describes PrintOS app benefits.",
                            "contentType": "Document",
                            "contentUpdateDate": "2019-07-03T08:35:14Z",
                            "parentDoc": "pdf_8834315_en-US-4.pdf",
                            "products": [
                                "HP Indigo 10000 Digital Press",
                                "HP Indigo 12000 Digital Press",
                            ],
                        },
                    ],
                }
            }
        },
    },
}
response_example_search.update(sample_exception)

# Example responses
response_examples_extras = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "documentID": "ish_9230172-9229960-16",
                    "render_link": "https://css.api.hp.com/knowledge/v2/render/6f9MBfc5mjTdAxi2Kb9+QiYuu9Hvi4fIarpLjO3hb3Q_hEJqA_dSTf48NoctmBGAobq52ZCGK3SZtmPHYBNAYa+q9ozEQtOdq9l6Xugo6Cj7of1BG1QLRIg0HG559CAjr7Dm2K6xTdlcMscvXv45DVk5pF6aLHiIPOo1xE88yfB+XnP4lImwlyVoZqZ1VjqtCqC_rhjsghIE_gxFTxaxWhF3mZY+1Hkno66EQm8V4wB0p+eTYgioP_aY4KpKcnPWigGCj2f6eZ6lDarptT784s8mjeewtsMv3XOmK_L_RNbuLhSkHu+pEKddViEgNaX23znzDYtAPfR2ZN2uDhKkxjNzwqbRJ3X2i_dds4WZXH+HtEpFfZreG3A_S4nWCBIYTo8MyOy02ZCYz49XiocoZz8erb_lYo5c33pJOx9HDJ0YxY_MxteHOEgOMQq3PU8mmCFrAdyyody6UKX8RvCBA7SEy+zVQEeqfVkY9a+JXhaYA9zAFreuVC1WS1WMgtoukV4uQgu_T1HQVMT6c4q8aeg1Au1UFJcHVyGH19nbycBIG8ADjlx7WMpxnSmofKpVY86DNDUEaiI8QOCdQubmZ9j+ZxSjdOO_EovDvKgEKsundv7lJ1YRMTXUWqHUfDPXCq14j0yPqD0FDQKGLe4VhgY77T70jAQukHZsdkFGehsuyA4xCYFi3OPaMiOgHaBcR7UIJyOCC1FePBIl7eqfYAe6BHiSRFL6l1lUwg1Ds8jS5kAOzL_nNefBTz7PJIXKvY8eOWm8ZOych4tWiiL8lNku0xXV5gVtEB5YANsCTdNhDE19+EBXIE8TH7rTr6WOt_ZWZ7ak4Mn141QUacY5RkyfteXOw7WbE3neKCg4iPV_oyOKL40UN5obqixZvVDUOpEGsylpTVUiJjwgm+0XpDdr6aAPbgk6TMysaXVWelSu+BqbQBEfhnEsWKn6fe2g8eWUwPi4wRGR579_xXPjII884vZqRF3iaPPS6Hyt4Qx6V6pv8qJ6aHcx5uYOzW8u8s3YbCB6o0jVhcS+Yen95olVyUEVIyRNg1_cNLdmdhBnq+eX85FGBi3biwpnWTUYPrb2alQVICtPU3xk56o5d5H+R5dE3lPT4GpkS8Nf+mAZGclF8i0yeFDSQkhKBzj2Nl3sWsM5rjN9+uUXR833zIw74mE9JcFBksOPti46Rj8hF3NzMdwwuRKV3Sm7qP7qWC353M15J5Ji6ThrozisrpoThSh_2tVNRPwAWm8FgyoWRUmIU1rH5Q6rHQjUzO_3I1clz3HOVDqIdeb4qGJkzJDt8jhAjbNB/ish_9230172-9229960-16",
                }
            }
        },
    },
}
response_examples_extras.update(sample_exception)

# Example response for bulk render URL API

response_examples_bulk = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "language": "en",
                        "documentID": ["pdf_9994661_en-US-2", "pdf_"],
                    },
                    "data": [
                        {
                            "documentid": "ish_9700653-9691233-16",
                            "success": True,
                            "render_link": "https://kaas.hpcloud.hp.com/pdf-nonpublic/pdf_9994661_en-US-2.pdf?Expires=1726154828&Signature=Eg9EqQn6LOYG67DI8yDk5UKUlkJPEbXVnUC6bSMQzrk7yAzLLeyf8jqeAjoBi86k7cXOP0jYywMSVa2cUA45lXSdimRpSaB~~3RXyZWJBd1NmwPy3NpPaCiszwXzf4ve9PzDIIaMQDtlcmQB7DQaDen6uc~YWMxBtUUy5ldpED-OvKDSMAL9PlMxdGP6G7tu0cLZkZjcdbdOfB63gXeqQtqbfvrE5ZjXjuS1JysSzQRaTCXyiISW-xlvKINj-33mzKmhkO8AudzMTNLYCZyFvrBB4C8wX9orWGI-Pxk~WEAw8qvsmAKFG0R24UTVfztpLhwik1mKzPxKMXuffhxRFw__&Key-Pair-Id=APKAIEP4ZT2OPKULVJXQ",
                            "error_message": None,
                            "language": "en-US",
                        },
                        {
                            "documentid": "pdf_",
                            "success": False,
                            "render_link": None,
                            "error_message": "Document not Found or not available for the given languageCode.",
                            "language": None,
                        },
                    ],
                }
            }
        },
    }
}

response_examples_bulk.update(sample_exception)
