from flask import Blueprint, jsonify, make_response
from controller.robot_controller import RobotController
from neural_network.model import Model
from capture.capture_module import CaptureModule


def construct_robot_blueprint(
        robotcontroller: RobotController,
        model: Model,
        table: int,
) -> Blueprint:

    robot_controller = Blueprint('robot_controller', __name__)

    @robot_controller.before_request
    def connect_robot():
        robotcontroller.connect()
        robotcontroller.robot.open_tool()

    @robot_controller.after_request
    def disconnect_robot(response):
        robotcontroller.to_disconnect()
        robotcontroller.disconnect()
        return response

    @robot_controller.route('/help', methods=['GET'])
    def robot_methods():
        return jsonify({
            0: {
                'title': 'Test Positions',
                'route': '.../test_position/<pos_key>/<move_type>',
                'http_method': 'GET',
                'desc': 'Allows to test bank positions for the robot.'
            },
            1: {
                'title': 'Get Position',
                'route': '.../position',
                'http_method': 'GET',
                'desc': 'Retrieves the actual robot Joint and Pose.'
            },
            2: {
                'title': 'Detect Board',
                'route': '.../detect',
                'http_method': 'GET',
                'desc': 'Requests the robot to detect the actual board.'
            },
            3: {
                'title': 'Remove Piece',
                'route': '.../remove_piece/<pos_key>',
                'http_method': 'GET',
                'desc': 'Requests the robot to remove a piece from the board.'
            },
            4: {
                'title': 'Place Queen',
                'route': '.../place_queen/<pos_key>/<queen_n>',
                'http_method': 'GET',
                'description': 'Requests the robot to place a queen.'
            },
            5: {
                'title': 'Capture Movement',
                'route': '.../capture/<pos_list>',
                'http_method': 'GET',
                'description': 'Requests the robot to move through the board.'
            },
        }), 200

    @robot_controller.route('/position', methods=['GET'])
    def position():
        joints, pose = robotcontroller.get_positions()
        return jsonify({
            'joints': joints.to_dict,
            'pose': pose.to_dict,
        }), 200

    @robot_controller.route('/test_position/<pos_key>/<move_type>')
    def test_position(pos_key, move_type):
        try:
            if move_type.lower() in ('c', 'cartesian'):
                robotcontroller._to_custom_coords(pos_key)
            else:
                robotcontroller._to_custom_pose(pos_key)
            response = make_response(
                'Moving to position',
                200,
            )
            return response
        except KeyError:
            bad_response = make_response(
                f'Key {pos_key} of type {move_type} not found',
                400,
            )
            return bad_response

    @robot_controller.route('/remove_piece/<pos_key>', methods=['GET'])
    def remove_piece(pos_key):
        robotcontroller.to_upperboard()
        try:
            robotcontroller.remove_piece_from_board(pos_key)
        except KeyError as err:
            return jsonify({'Error': str(err)}), 400
        finally:
            robotcontroller.to_upperboard()
        return jsonify({'ok': f'piece removed from {pos_key}'}), 200

    @robot_controller.route('/place_queen/<pos_key>/<queen_n>')
    def place_queen(pos_key, queen_n):
        robotcontroller.to_upperboard()
        try:
            qn = int(queen_n)
            robotcontroller.place_queen(
                target_location=pos_key,
                queen=qn,
            )
        except KeyError as err:
            return jsonify({'Error': str(err)}), 400
        except TypeError as err:
            return jsonify({'Error': str(err), 'arg': queen_n}), 400
        finally:
            robotcontroller.to_upperboard()
        return jsonify({'ok': f'Queen placed at {pos_key}'})

    @robot_controller.route('/capture/<pos_list>', methods=['GET'])
    def capture(pos_list):
        robotcontroller.to_upperboard()
        pos_list_keys = pos_list.lower().split(';')
        if len(pos_list_keys) < 2:
            err_dict = {
                'Error': 'You must pass at least 2 positions',
                'details': 'Each argument must be divided by ;'
                }
            return jsonify(err_dict), 400
        valid = robotcontroller.check_valid_keys(*pos_list_keys)
        if not valid:
            return jsonify({'Error': 'Invalid positions'}), 400
        try:
            robotcontroller.capture_piece(
                origin=pos_list_keys[0],
                targets=pos_list_keys[1:],
            )
        except KeyError as err:
            return jsonify({'Error': err}), 400
        finally:
            robotcontroller.to_upperboard()
        return jsonify({'ok': 'Robot moved sucessfully'}), 200

    @robot_controller.route('/detect', methods=['GET'])
    def detect():
        robotcontroller.to_upperboard()
        img = None
        count = 0
        # Table: Kinova => 1; KAnova => 2
        # Camera: Kinova => 0; KAnova => 1
        cam_idx = 0
        if robotcontroller.move_map.table == 2:
            cam_idx = 1
        capture_module = CaptureModule(cam_idx)
        while img is None:
            img = capture_module.capture_opencv()
            # TODO: find a way to kill a running instance of a singleton
            count += 1
        capture_module.video_capture.release()
        predict_list = model.predict_from_opencv(img, table)
        return jsonify({'ok': predict_list}), 200

    @robot_controller.route('/disconnect', methods=['GET'])
    def to_disconnect():
        robotcontroller.to_disconnect()
        return jsonify({'ok': 200}), 200

    return robot_controller
