import yaml  # imports the yaml module, which allows working with YAML files. YAML is a human-readable data serialization format often used for configuration files


class SettingsParser:  # define class, which is intended to handle loading settings from a YAML file

    # defines a method. The method takes one argument: configfname, which represents the filename of the YAML configuration file to load
    def load_from_file(self, configfname):

        # opens the specified file (configfname) in read mode ('r'). The file object is assigned to the variable f
        with open(configfname, 'r') as f:
            # yaml.safe_load() parses the YAML data and returns a Python dictionary containing the loaded settings.The resulting dictionary is assigned to the variable "params"
            params = yaml.safe_load(f)
        return params  # returns the "params" dictionary, which contains the loaded settings
# pega o arquivo de configs yml e converte ele para um dicionário para o python utilizar as configrações definidas de fato no código
