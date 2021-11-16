import os
import re
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D
from tensorflow.keras.layers import Dropout, UpSampling2D, add
from skimage.transform import resize, rescale
from tensorflow.keras.models import Model
from tensorflow.keras import regularizers
import matplotlib.pyplot as plt
import numpy as np
import math
import shutil
from zipfile import ZipFile
np.random.seed(0)

SOURCE_PARENT_DIR = './dataset/cars_train/'
DATA_DIR = './dataset/cars_train/data'
TUNED_OPTIMAL_WEIGHTS_AUTOENCODER = './dataset/sr.img_net.mse.weights.best.hdf5'
TUNED_OPTIMAL_WEIGHTS_ENCODER = './dataset/encoder_weights.hdf5'
EPOCHS = 4
BATCH_SIZE = 256
ACTIVATOR = 'relu'

def unpack_data(status=False):
    if(status):
        os.mkdir(SOURCE_PARENT_DIR+'data')
        print('Unzipping the Dataset')
        files = [file for file in os.listdir(SOURCE_PARENT_DIR) if file.endswith('.zip')]
        for file in files:
            with ZipFile(SOURCE_PARENT_DIR+file, 'r') as zipObj:
                zipObj.extractall(DATA_DIR)
        for dirName in os.listdir(DATA_DIR):
            for file in os.listdir(DATA_DIR+'/'+dirName):
                filepath = DATA_DIR+'/'+dirName+'/'+file
                shutil.move(filepath, DATA_DIR)
            os.rmdir(DATA_DIR+'/'+dirName)
        print('Dataset Extracted Successfully!')



def get_encoder(input_layer, activator, regularizer_act):
    layer1 = Conv2D(64, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(input_layer)
    layer2 = Conv2D(64, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer1)
    layer3 = MaxPooling2D(padding='same')(layer2)
    layer3 = Dropout(0.3)(layer3)
    layer4 = Conv2D(128, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer3)
    layer5 = Conv2D(128, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer4)
    layer6 = MaxPooling2D(padding='same')(layer5)

    layer7 = Conv2D(256, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer6)
    return Model(input_layer, layer7)


def get_decoder(input_layer, activator, regularizer_act):
    layer1 = Conv2D(64, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(input_layer)
    layer2 = Conv2D(64, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer1)
    layer3 = MaxPooling2D(padding='same')(layer2)
    layer3 = Dropout(0.3)(layer3)
    layer4 = Conv2D(128, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer3)
    layer5 = Conv2D(128, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer4)
    layer6 = MaxPooling2D(padding='same')(layer5)

    layer7 = Conv2D(256, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer6)
    layer8 = UpSampling2D()(layer7)

    layer9 = Conv2D(128, (3, 3), padding='same', activation=activator,
                    activity_regularizer=regularizer_act)(layer8)
    layer10 = Conv2D(128, (3, 3), padding='same', activation=activator,
                     activity_regularizer=regularizer_act)(layer9)
    layer11 = add([layer5, layer10])
    layer12 = UpSampling2D()(layer11)
    layer13 = Conv2D(64, (3, 3), padding='same', activation=activator,
                     activity_regularizer=regularizer_act)(layer12)
    layer14 = Conv2D(64, (3, 3), padding='same', activation=activator,
                     activity_regularizer=regularizer_act)(layer13)
    layer15 = add([layer14, layer2])

    output_layer = Conv2D(3, (3, 3), padding='same', activation=activator,
                          activity_regularizer=regularizer_act)(layer15)
    autoencoder = Model(input_layer, output_layer)
    autoencoder_hfenn = Model(input_layer, output_layer)
    return autoencoder, autoencoder_hfenn


def get_train_batches(just_load_dataset=False):
    current_batch = 0
    curr_batch_ind = 0
    max_batches = -1
    x_trainList = []
    x_train_downList = []
    x_train_n = []
    x_train_down = []

    for root, dirnames, filenames in os.walk(DATA_DIR):
        for filename in filenames:
            if re.search(r"\.(jpg|jpeg|JPEG|png|bmp|tiff)$", filename):
                if(curr_batch_ind == max_batches):
                    return x_train_n, x_train_down
                filepath = os.path.join(root, filename)
                image = plt.imread(filepath)
                if(len(image.shape) > 2):
                    image_reshaped = resize(image, (256, 256))
                    x_trainList.append(image_reshaped)
                    image_down = rescale(image_reshaped, 2)
                    x_train_downList.append(rescale(image_down, 0.5))
                    current_batch += 1
                    if(current_batch == BATCH_SIZE):
                        curr_batch_ind += 1
                        x_train_n = np.array(x_trainList)
                        x_train_down = np.array(x_train_downList)

                        if(just_load_dataset):
                            return x_train_n, x_train_down

                        print(f'Training Batch: {curr_batch_ind} of {BATCH_SIZE}')

                        autoencoder.fit(x_train_down, x_train_n, epochs=EPOCHS,
                                        batch_size=10, shuffle=True,
                                        validation_split=0.15)

                        x_trainList = []
                        x_train_downList = []
                        current_batch = 0
    return x_train_n, x_train_down

def print_decorator(func):
    def wrapper(*args):
        print('*' * 100)
        func(*args)
        print('*' * 100)
    return wrapper

@print_decorator
def print_menu():
    print('Which operation do you want to perform?')
    print('1. Train the model')
    print('2. Test the model')

def plot_graph(x_train_down, x_train_n, res_image,image_index ):
    plt.figure(figsize=(100, 100))
    ax = plt.subplot(10, 10, 1)
    plt.imshow(x_train_down[image_index])
    plt.show()
    ax = plt.subplot(10, 10, 2)
    plt.imshow(x_train_n[image_index])
    plt.show()
    ax = plt.subplot(10, 10, 3)
    plt.imshow(res_image[image_index])
    plt.show()

@print_decorator
def print_summary(encoder_text, encoder):
    print('{} Initialized'.format(encoder_text))
    encoder.summary()
    
if __name__ == '__main__':
    print_menu()
    option_num = int(input('Enter you option (1/2): '))
    if(option_num == 1):
        just_loaddata = False
    elif(option_num == 2):
        just_loaddata = True
    else:
        print('Invalid Option')

    if 'data' not in os.listdir(SOURCE_PARENT_DIR):
        unpack_data(True)

    regularizer_act = regularizers.l1((10 * math.e) - 10)
    input_layer = Input(shape=(256, 256, 3))
    encoder = get_encoder(input_layer, ACTIVATOR, regularizer_act)
    autoencoder, autoencoder_hfenn = get_decoder(input_layer, ACTIVATOR,
                                                regularizer_act)
    just_loaddata = True
    print_summary('Encoder', encoder)
    print_summary('Decoder', autoencoder)
    print("This might take a while!")
    x_train_n, x_train_down = get_train_batches(just_load_dataset=just_loaddata)
    autoencoder.load_weights(TUNED_OPTIMAL_WEIGHTS_AUTOENCODER)
    encoder.load_weights(TUNED_OPTIMAL_WEIGHTS_ENCODER)
    encoded_image = encoder.predict(x_train_down)
    res_image = np.clip(autoencoder.predict(x_train_down), 0.0, 1.0)
    image_index = np.random.randint(0, 255)
    plot_graph(x_train_down, x_train_n, res_image,image_index)
