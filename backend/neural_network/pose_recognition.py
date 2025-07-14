import csv
import copy
import itertools
from tflite_runtime.interpreter import Interpreter
import numpy as np
import json
from instructions import gesture_buffer

class PoseRecognizer(object):
    def __init__(self, model_path='model/keypoint_classifier.tflite', label_path='model/keypoint_classifier_label.csv'):
        self.keypoint_classifier, self.keypoint_classifier_labels = self.load_model(model_path=model_path, label_path=label_path)
        # Inicializar el buffer de gestos con 20 frames y un umbral del 80%
        # Inicialización del buffer de gestos
        with open('config_pose.json', 'r') as config_file:
            config = json.load(config_file)
        self.buffer = gesture_buffer.GestureBuffer(buffer_len=config['constants']['buffer_length'])
        
    def recognize_pose(self, results, debug_image):
        gesture = -1

        # if results is None or debug_image is None or results.multi_pose_landmarks is None:
    
        if results is None or debug_image is None or results.pose_landmarks is None:
            return gesture, self.keypoint_classifier_labels

        pose_landmarks = results.pose_landmarks
        landmark_list = self.calc_landmark_list(debug_image, pose_landmarks.landmark)
        pre_processed_landmark_list = self.pre_process_landmark(landmark_list)

        # Obtener el ID del gesto
        pose_sign_id = self.keypoint_classifier(pre_processed_landmark_list)

        # Agregar al buffer para validar consistencia
        self.buffer.add_gesture(pose_sign_id)

        # Obtener el gesto consistente (si lo hay)
        gesture = self.buffer.get_gesture()

        return gesture, self.keypoint_classifier_labels

    def translate_gesture_id_to_name(self, gesture_id):
        """Traduce el ID del gesto a su nombre."""
        if gesture_id is None or gesture_id == -1:
            return 'No gesture'  # Manejar gestos no válidos o sin detectar

        # Asegurar que el ID esté dentro del rango válido
        if gesture_id >= len(self.keypoint_classifier_labels):
            return 'Unknown gesture'

        return self.keypoint_classifier_labels[gesture_id]
    
    def calc_landmark_list(self, image, landmarks):
        """Calcula la lista de landmarks con las coordenadas X, Y, Z."""
        image_width, image_height = image.shape[1], image.shape[0]

        landmark_point = []

        # Filtrar los landmarks del torso y extremidades
        INCLUDED_LANDMARKS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]


        for idx, landmark in enumerate(landmarks):
            if idx in INCLUDED_LANDMARKS:
                landmark_x = min(int(landmark.x * image_width), image_width - 1)
                landmark_y = min(int(landmark.y * image_height), image_height - 1)
                landmark_z = landmark.z  # Incluimos la profundidad Z

                landmark_point.append([landmark_x, landmark_y, landmark_z])

        return landmark_point



    def load_model(self, model_path, label_path):
        self.keypoint_classifier = KeyPointClassifier(model_path=model_path)

        with open(label_path, encoding='utf-8-sig') as f:
            keypoint_classifier_labels = csv.reader(f)
            self.keypoint_classifier_labels = [row[0] for row in keypoint_classifier_labels]

        return self.keypoint_classifier, self.keypoint_classifier_labels


    def pre_process_landmark(self, landmark_list):
        """Preprocesa los landmarks para convertirlos a coordenadas relativas y normalizadas."""
        temp_landmark_list = copy.deepcopy(landmark_list)

        # Convertir a coordenadas relativas usando X, Y, Z
        base_x, base_y, base_z = 0, 0, 0
        for index, landmark_point in enumerate(temp_landmark_list):
            if index == 0:  # Tomar el primer punto como referencia base
                base_x, base_y, base_z = landmark_point[0], landmark_point[1], landmark_point[2]

            temp_landmark_list[index][0] = landmark_point[0] - base_x
            temp_landmark_list[index][1] = landmark_point[1] - base_y
            temp_landmark_list[index][2] = landmark_point[2] - base_z

        # Convertir la lista a una lista unidimensional
        temp_landmark_list = list(itertools.chain.from_iterable(temp_landmark_list))

        # Normalización usando el máximo valor absoluto (incluyendo Z)
        max_value = max(list(map(abs, temp_landmark_list)))

        def normalize_(n):
            return n / max_value if max_value != 0 else 0  # Evitar división por cero

        # Aplicar la normalización
        temp_landmark_list = list(map(normalize_, temp_landmark_list))

        return temp_landmark_list

class KeyPointClassifier(object):
    def __init__(self, model_path, num_threads=1):
        self.interpreter = Interpreter(model_path=model_path, num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(self, landmark_list):
        input_details_tensor_index = self.input_details[0]['index']
        self.interpreter.set_tensor(input_details_tensor_index, np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()

        output_details_tensor_index = self.output_details[0]['index']

        result = self.interpreter.get_tensor(output_details_tensor_index)

        result_index = np.argmax(np.squeeze(result))

        return result_index
