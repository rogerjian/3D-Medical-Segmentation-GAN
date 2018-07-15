# Arda Mavi

import os
import numpy as np
from os import listdir
from random import shuffle
from get_dataset import read_npy_dataset, split_npy_dataset
from get_models import get_segment_model, get_Discriminator, get_GAN, get_Generator, save_model
from keras.callbacks import ModelCheckpoint, TensorBoard

epochs = 25
batch_size = 4
test_size = 0.2

# Training Segment Model:
def train_seg_model(model, splitted_npy_dataset_path, test_path, epochs):
    test_XY = np.load(test_path+'/test.npy')
    X_test, Y_test = test_XY[0], test_XY[1]

    batch_dirs = listdir(splitted_npy_dataset_path)
    len_batch_dirs = len(batch_dirs)

    if not os.path.exists('Data/Checkpoints/'):
        os.makedirs('Data/Checkpoints/')
    checkpoints = []
    checkpoints.append(ModelCheckpoint('Data/Checkpoints/best_weights.h5', monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=True, mode='auto', period=1))
    checkpoints.append(TensorBoard(log_dir='Data/Checkpoints/./logs', histogram_freq=0, write_graph=True, write_images=False, embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None))

    for epoch in range(epochs):
        print('Epoch: {0}/{1}'.format(epoch+1, epochs))
        model.fit_generator(data_gen(splitted_npy_dataset_path), steps_per_epoch=batch_size, epochs=int(len_batch_dirs/batch_size), callbacks=checkpoints)

        # TODO: Optimize memory uses:
        """
        scores = model.evaluate(X_test, Y_test)
        print('Test loss:', scores[0], 'Test accuracy:', scores[1])
        """
    return model

# Training GAN:
def train_gan(Generator, Encoder, Discriminator, GAN, splitted_npy_dataset_path, test_path, epochs):
    # Dataset sample sharing:
    batch_dirs = listdir(splitted_npy_dataset_path)
    batch_num = len(batch_dirs)

    test_XY = np.load(test_path+'/test.npy')
    X_test, Y_test = test_XY[0], test_XY[1]

    data_generator = data_gen(splitted_npy_dataset_path)

    for epoch in range(epochs):
        print('Epoch: {0}/{1}'.format(epoch+1, epochs))

        # Discriminator Training:
        for i in range(int(batch_num/4)):
            # Getting generated data:
            getted_generator_data = next(data_generator)
            generator_pred = Generator.predict(getted_generator_data[0])

            # Getting real data:
            getted_real_data = next(data_generator)

            # Getting batch:
            # Xs:
            dis_batch_X1 = np.concatenate((getted_generator_data[0], getted_real_data[0]), axis=0)
            dis_batch_X2 = np.concatenate((generator_pred, getted_real_data[1]), axis=0)
            # Ys:
            dis_batch_Y = np.concatenate((np.zeros((getted_generator_data[0].shape[0], 1)), np.ones((getted_real_data[0].shape[0], 1))), axis=0)

            Discriminator.trainable = True
            Discriminator.fit([dis_batch_X1, dis_batch_X2], dis_batch_Y, batch_size=1, epochs=1, shuffle=True)

        # Generator Training:
        for i in range(int(sample_num/2)):
            # Getting generated data:
            getted_generator_data = next(generator)

            # Getting batch:
            # Xs:
            gan_batch_X = getted_generator_data[0]
            # Ys:
            gan_batch_Y = np.ones((gan_batch_X.shape[0], 1))

            Discriminator.trainable = False
            Encoder.trainable = True
            GAN.fit(gan_batch_X, gan_batch_Y, batch_size=1, epochs=1, shuffle=True)

        # TODO: Optimize memory uses:
        """
        scores = Generator.evaluate(X_test, Y_test)
        print('Test loss:', scores[0], 'Test accuracy:', scores[1])
        """

    return Generator, Encoder, Discriminator

def data_gen(splitted_npy_dataset_path):
    batch_dirs = listdir(splitted_npy_dataset_path)
    while True:
        shuffle(batch_dirs)
        for batch_path in batch_dirs:
            batch_XY = np.load(splitted_npy_dataset_path+'/'+batch_path)
            X_batch, Y_batch = batch_XY[0], batch_XY[1]
            yield X_batch, Y_batch

def main(train_gan_model = True):
    if train_gan_model:
        # Getting Generator:
        Generator, Encoder = get_segment_model(data_shape = (256, 256, 32, 1))
        Discriminator = get_Discriminator(input_shape_1 = (256,256,32,1), input_shape_2 = (256, 256, 32, 1), Encoder = Encoder)
        GAN = get_GAN((256, 256, 32, 1), Generator, Discriminator)

        # Saving non-trained models:
        save_model(Generator, path='Data/GAN-Models/Generator/', model_name = 'model', weights_name = 'weights')
        save_model(Encoder, path='Data/GAN-Models/Encoder/', model_name = 'model', weights_name = 'weights')
        save_model(Discriminator, path='Data/GAN-Models/Discriminator/', model_name = 'model', weights_name = 'weights')
        print('Non-Trained model saved to "Data/GAN-Models"!')

        # Train:
        Generator, Encoder, Discriminator = train_gan(Generator, Encoder, Discriminator, GAN, splitted_npy_dataset_path='Data/npy_dataset/splitted_npy_dataset', test_path = 'Data/npy_dataset/test_npy', epochs = 100)

        # Saving trained models:
        save_model(Generator, path='Data/GAN-Models/Generator/', model_name = 'model', weights_name = 'weights')
        save_model(Encoder, path='Data/GAN-Models/Encoder/', model_name = 'model', weights_name = 'weights')
        save_model(Discriminator, path='Data/GAN-Models/Discriminator/', model_name = 'model', weights_name = 'weights')
        print('Trained model saved to "Data/GAN-Models"!')
        return Generator
    else:
        segment_model, _ = get_segment_model(data_shape = (256, 256, 32, 1))
        print(segment_model.summary())
        save_model(segment_model, path='Data/Model/', model_name = 'model', weights_name = 'weights')
        print('Non-Trained model saved to "Data/Model"!')
        model = train_seg_model(segment_model, splitted_npy_dataset_path='Data/npy_dataset/splitted_npy_dataset', test_path = 'Data/npy_dataset/test_npy', epochs = 25)
        save_model(segment_model, path='Data/Model/', model_name = 'model', weights_name = 'weights')
        print('Trained model saved to "Data/Model"!')
        return segment_model

if __name__ == '__main__':
    main(train_gan_model = True)
