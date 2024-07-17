from json import load, dumps
from robots.pose import Pose
from robots.joint import Joint
from enum import Enum


class RobotTableEnum(Enum):

    KINOVA = '_r1'
    KANOVA = '_r2'


class MoveBank:
    """Class used to keep and retrieve the movement references
    for the Robot. Loads and stores the references in a `JSON`
    file."""

    __instance = None
    filepath = r"src\movebank\positions_kinova.json"

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(
                MoveBank,
                cls).__new__(cls)
        return cls.__instance

    def __init__(
            self,
            robot_table: RobotTableEnum = RobotTableEnum.KINOVA,
    ) -> None:
        bankdict = self.__load_bank()
        self.__bankdict = bankdict
        self.__tablekey = robot_table.value

    def __load_bank(self) -> dict[str, dict[str, list[float]]]:
        """Loads the `MoveBank` from the json file."""
        with open(MoveBank.filepath, 'r') as file:
            json_object = load(file)
            return json_object

    def __update_bank(self) -> None:
        """Updates the `.json` file used to populate the bank."""
        jsonstr = dumps(self.__bankdict, indent=4, sort_keys=True)
        with open(MoveBank.filepath, 'w') as outfile:
            outfile.write(jsonstr)
            print('File Updated')

    def __str_to_floatlist(self, string: str) -> list[float]:
        """Parses the string structure to a proper list of floats."""
        values = string[1:-2].split(',')
        return [float(v) for v in values]

    def get_cartesian(self, key: str) -> Pose:
        """Gets the cartesian reference of a given key."""
        if len(key) == 2:
            key = f'{key}{self.__tablekey}'
        if key in self.__bankdict:
            str_list = self.__bankdict[key]['cartesian']
            float_list = self.__str_to_floatlist(str_list)
            pose = Pose(*float_list)
            return pose
        else:
            raise KeyError(f'key {key} not in MoveBank')

    def get_joints(self, key: str) -> Joint:
        """Gets the joints reference of a given key."""
        if key in self.__bankdict:
            str_list = self.__bankdict[key]['joints']
            float_list = self.__str_to_floatlist(str_list)
            joint = Joint(*float_list)
            return joint
        else:
            raise KeyError(f'key {key} not in MoveBank')

    def _record_positions(
        self,
        pos_key: str,
        joint: Joint,
        pose: Pose,
    ) -> None:
        """Updates the internal bank dict object of an instance
        and the file used to load the bank."""
        self.__bankdict[pos_key] = {
            'cartesian': str(pose.to_list),
            'joints': str(joint.to_list),
        }
        self.__update_bank()
