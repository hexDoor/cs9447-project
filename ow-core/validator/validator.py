import jsonschema
import yaml
import json
import os
import argparse

# Arguments Engine
parser = argparse.ArgumentParser(description="OverWatch Rules Validator")
parser.add_argument(
    "rules_path",
    metavar="path",
    type=str,
    nargs="?",
    default="rules.yaml",
    help='Path to rules yaml | fileName of rules yaml file if autofind flag is set | Default: "rules.yaml"',
)
parser.add_argument(
    "--autofind",
    dest="autofind",
    action="store_true",
    help="Enables autofinding of filename in <rules_path>",
)

# Path to Schema
SCHEMA_PATH = "ow-core/validator/schema.yaml"

# Custom Exception Handling for smoother debugging
class DuplicateNameException(Exception):
    def __init__(self, message):
        super().__init__(message)


class OverwatchValidator:
    def __init__(self, rule_path, autofind):
        self.rule_path = rule_path
        self.autofind = autofind

    # Taken from: https://stackoverflow.com/questions/1724693/find-a-file-in-python
    # Used to find path of 'rules.yaml' file in the root of user's project directory.
    # Intelligently does this (no hardocded paths), thus, it does not matter whether user is on Windows or Linux
    def find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    def load_rules(self):
        filepath = (
            str(self.find(self.rule_path, os.path.abspath(os.curdir)))
            if self.autofind
            else self.rule_path
        )
        with open(filepath) as f:
            rules = yaml.load(f, Loader=yaml.FullLoader)
        return json.dumps(rules)

    def validate_rules_structure(self):
        with open(SCHEMA_PATH) as f:
            schema = yaml.load(f, Loader=yaml.FullLoader)
            try:
                rules = self.load_rules()
                cleaned_rules = json.loads(rules)
                jsonschema.validate(instance=cleaned_rules[0], schema=schema)
            except (jsonschema.ValidationError, KeyError) as error:
                return False, "Invalid Rules File"
            return True, "Valid Rules File"

    def validate_alarm_attributes(self):
        rules = self.load_rules()
        cleaned_rules = json.loads(rules)
        alarmNames = []
        for rule in cleaned_rules:
            if rule["Alarm"]["AlarmName"] not in alarmNames:
                alarmNames.append(rule["Alarm"]["AlarmName"])
            else:
                raise DuplicateNameException("AlarmName must be unique.")
        return alarmNames
    def validate_metric_attributes(self):
        rules = self.load_rules()
        cleaned_rules = json.loads(rules)
        metricNames = []
        for rule in cleaned_rules:
            if rule["Metric"]["filterName"] not in metricNames:
                metricNames.append(rule["Metric"]["filterName"])
            else:
                raise DuplicateNameException("filterName must be unique.")
        return metricNames
    # get_local_alarm_names and get_local_metric_names are simply helper functions for developers
    # these two functions are NOT used in validation step
    def get_local_alarm_names(self):
        result = []
        rules = self.load_rules()
        cleaned_rules = json.loads(rules)
        for rule in cleaned_rules:
            result.append(rule["Metric"]["filterName"])
        return result

    def get_local_metric_names(self):
        result = []
        rules = self.load_rules()
        cleaned_rules = json.loads(rules)
        for rule in cleaned_rules:
            result.append(rule["Alarm"]["AlarmName"])
        return result

    def validate(self):
        # Any other functions that are apart of the validation process add it here
        self.validate_alarm_attributes()
        self.validate_metric_attributes()
        is_valid, msg = self.validate_rules_structure()
        # TODO: perhaps actual and real error messaging?
        print(msg)
        if not is_valid:
            exit(1)
        exit(0)


if __name__ == "__main__":
    # parse the arguments
    args = parser.parse_args()

    # validator class instance
    validator = OverwatchValidator(args.rules_path, args.autofind)
    # if path given, attempt to validate
    validator.validate()
