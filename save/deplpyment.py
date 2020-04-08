from tools import get_json

class DeploymentStage(object):
    """
    Represent deployment for a given stage
    """
    def __init__(self, config_dict, deployment, parent=None, stage=None):
        self.config_dict = config_dict
        self.stage = stage
        self.deployment = deployment
        self.parent = parent
    
    def _get_value(self, key):
        # get the value of a config key, and 
        if key in self.config_dict:
            return self.config_dict[key]
        
        if self.parent is None:
            return None
        
        return self.parent.get_value(key)
    
    @property
    def home_dir(self):
        # home directory of the source code
        return self._get_value("home_dir")

    @property
    def cmd(self):
        # the path to the command to run the app, the default command is "run.sh"
        return self._get_value("home_dir") or "run.sh"

   @property
    def use_python3(self):
        # using python3?
        return self._get_value("use_python3")
    
   @property
    def configurations(self):
        # using python3?
        return self._get_value("configurations")

class Deployment(object):
    def __init__(self, name, config):
        self.config = config
        self.name = name
        self.stage_dict = {} # key is stage name, value is DeploymentStageConfig

        # parse the config    
        base_config_dict = {}          # for base config_dict
        config_dict_by_stage_dict = {} # key is stage, value is config_dict
        
        for key, value in self.config.items():
            if key.startswith("_") and key.endswith("_") and len(key)>2:
                stage = key[1:-1]
                config_dict_by_stage_dict[stage] = value
            else:
                base_config_dict[key] = value
        
        self.base = DeploymentStage(base_config_dict, self)
        for stage, stage_config_dict in config_dict_by_stage_dict.items():
            self.stage_dict[stage] = DeploymentStage(
                stage_config_dict, self, parent=base_config, stage=stage
            )
        
        


