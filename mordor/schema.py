from jsonschema import validate, validators, Draft7Validator

models = {
    "Host": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique ID for the host"
            },
            "type": {
                "type": "string",
                "enum": ["ssh", "container"],
                "description": """\
Type of the host, 
    ssh      : It is a system you can connect via ssh
    container: It is a docker container, you can connect to the host the container lives. The host is specified in host field.
"""
            },
            "host": {
                "type": "string",
                "descrption": "The host name for the target, check your ~/.ssh/config"
            },
            "per_user": {
                "type": "boolean",
                "description": "If mordor is installed globally, this is false, otherwise this is true"
            },
            "python2": {
                "type": "string",
                "description": "Specify the python2 bin if python2 is installed"
            },
            "python3": {
                "type": "string",
                "description": "Specify the python3 bin if python3 is installed"
            },
            "virtualenv": {
                "type": "string",
                "description": "Specify the virtualenv bin. Only used when using python2"
            },
            "container": {
                "type": "string",
                "description": "The docker container name, you must provide this if type is container"
            },
        },
        "additionalProperties": False,
        "required": ["id", "type", "host", "per_user"]
    },
    "Compartment": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique ID for the compartment"
            },
            "hosts": {
                "type": "array",
                "item": {
                    "type": [
                        "string", 
                    ]
                },
                "description": "List of host id belongs to this compartment."
            },
        },
        "additionalProperties": False,
        "required": ["id", "hosts"]
    },
    "Application": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique ID for the application"
            },
            "home_dir": {
                "type": "string",
                "description": "home directory for the source code of this application"
            },
            "support_python2": {
                "type": "boolean",
                "description": "Does this application support python2?"
            },
            "support_python3": {
                "type": "boolean",
                "description": "Does this application support python3?"
            },
        },
        "additionalProperties": False,
        "required": ["id", "home_dir"]
    },
    "Configuration": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique ID for the Configuration"
            },
            "location": {
                "type": "string",
                "description": "filename for the configuration"
            },
            "type": {
                "type": "string",
                "enum": ["raw", "template"],
                "description": """\
type of the configuration\
    raw     : just copy the file over.
    template: the file is a template, the rendered result will be copied over
"""
            },
        },
        "additionalProperties": False,
        "required": ["id", "location", "type"]
    },
    "AnonymouseConfiguration": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "filename for the configuration"
            },
            "type": {
                "type": "string",
                "enum": ["raw", "template"],
                "description": """\
type of the configuration\
    raw     : just copy the file over.
    template: the file is a template, the rendered result will be copied over
"""
            },
        },
        "additionalProperties": False,
        "required": ["location", "type"]
    },
    "Deployment": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique ID for the deployment"
            },
            "application": {
                "type": "string",
                "description": "The application id for deployment. The deployment will deploy this application"
            },
            "compartment": {
                "type": "string",
                "description": "The conpartment id this application will deploy to"
            },
            "hosts": {
                "type": "array",
                "item": {
                    "type": [
                        "string", 
                    ]
                },
                "description": "List of host id this deployment will deploy to, if missing, then mean all host belong to the compartment"
            },
            "use_python": {
                "type": "string",
                "enum": ["python2", "python3"],
                "description": "if it is python2, then this deployment will use python2, if it is python3, then this deployment will use python3"
            },
            "configurations": {
                "type": "array",
                "item": {
                    "type": [
                        "string", 
                        {"$ref": "#/models/AnonymousConfiguration"}
                    ]
                },
                "description": "List of configurations this deployment will use"
            },
        },
        "additionalProperties": False,
        "required": ["id", "application", "compartment", "use_python"]
    },
}

schema = {
    "models": models,
    "type": "object",
    "properties": {
        "hosts": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Host"
            }
        },
        "compartments": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Compartment"
            }
        },
        "applications": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Application"
            }
        },
        "configurations": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Configuration"
            }
        },
        "deployments": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Deployment"
            }
        },
        "deployments": {
            "type": "array",
            "items": {
                "$ref": f"#/models/Deployment"
            }
        },
    },
    "additionalProperties": False,
}

def validate_config(config):
    MyValidator = validators.extend(
        Draft7Validator,
    )
    my_validator = MyValidator(schema=schema)
    my_validator.validate(config)
