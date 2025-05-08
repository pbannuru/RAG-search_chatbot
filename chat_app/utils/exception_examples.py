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


standard_errors = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1001",  # Example: Invalid input
                    "message": "Bad Request"
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1002",
                    "message": "Invalid input. Please check your request."
                }
            }
        }
    },
    429: {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1003",
                    "message": "Too many requests. Please try again later."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E2001",
                    "message": "Unexpected server error. Please contact support."
                }
            }
        }
    },
}

# Example responses
response_example_search = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 5,
                        "source": ["all"],
                        "query": "million impressions",
                        "device": "HP Indigo WS6000 Digital Press",
                        "persona": "engineer",
                        "domain": "indigo"
                    },
                    "data": {
                        "content": "The term \"million impressions\" in the context of HP Indigo presses typically refers to the preventive maintenance (PM) service that is performed after a certain number of impressions (prints) have been made by the press. Here are some key points...",
                        "question": "million impressions",
                        "citations": "[Document(metadata={'technicalLevel': '', 'disclosureLevel': '287477763180518087286275037723076', 'contentTypeHeader': 'Product Support', 'persona': 'Operator', 'parentDoc': None, 'description': 'HP Indigo WS6000 Digital Press, HP Indigo WS6600 Digital Press, HP Indigo WS6600p Digital Press, HP Indigo WS6800 Digital Press, HP Indigo WS6800p Digital Press, HP Indigo 6900 Digital Press, HP Indigo 6r Digital Press, HP Indigo W7200 Digital Press, HP Indigo W7250 Digital Press, HP Indigo 8000 Digital Press', 'language': 'en', 'store': 'UDPManuals', 'title': '12 Million Impression - Preventive Maintenance for Operator Level 3 — CA493-04670 Rev 01', 'docSource': 'UDP', 'products': ['HP Indigo WS6600p Digital Press', 'HP Indigo WS6800 Digital Press', 'HP Indigo 6r Digital Press']})]"
                    }
                }
            }
        },
    },
}
response_example_search.update(standard_errors)

