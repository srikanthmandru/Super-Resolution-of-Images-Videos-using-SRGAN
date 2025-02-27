# -*- coding: utf-8 -*-
"""srgan_model.py

"""
import tensorflow as tf
from tensorflow.python.keras.layers import Add, BatchNormalization, Conv2D, Dense, Flatten, Input, LeakyReLU, PReLU, Lambda
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.applications.vgg19 import VGG19


def pixel_shuffle(scale):
    return lambda x: tf.nn.depth_to_space(x, scale)


def upsample(x_in, num_filters):
    x = Conv2D(num_filters, kernel_size=3, padding='same')(x_in)
    x = Lambda(pixel_shuffle(scale=2))(x)
    return PReLU(shared_axes=[1, 2])(x)


def res_block(x_in, num_filters, momentum=0.8, is_training = False):
    x = Conv2D(num_filters, kernel_size=3, padding='same')(x_in)
    x = BatchNormalization(momentum=momentum)(x)
    x = PReLU(shared_axes=[1, 2])(x)
    x = Conv2D(num_filters, kernel_size=3, padding='same')(x)
    x = BatchNormalization(momentum=momentum)(x)
    x = Add()([x_in, x])
    return x


def generator(x_in, mode, weight_decay=2.5e-5, num_filters=64, num_res_blocks=16):
    is_training = (mode == tf.estimator.ModeKeys.TRAIN)
    if isinstance(x_in, dict):  # For serving
        x_in = x_in['feature']

    x = Conv2D(num_filters, kernel_size=9, padding='same')(x_in)
    x = x_1 = PReLU(shared_axes=[1, 2])(x)

    for _ in range(num_res_blocks):
        x = res_block(x, num_filters, is_training = is_training)

    x = Conv2D(num_filters, kernel_size=3, padding='same')(x)
    x = BatchNormalization()(x)
    x = Add()([x_1, x])

    x = upsample(x, num_filters * 4)
    x = upsample(x, num_filters * 4)

    x = Conv2D(3, kernel_size=9, padding='same', activation='tanh')(x)

    # return Model(x_in, x)
    return x



def discriminator_block(x_in, num_filters, strides=1, batchnorm=True, momentum=0.8, is_training = False):
    x = Conv2D(num_filters, kernel_size=3, strides=strides, padding='same')(x_in)
    if batchnorm:
        x = BatchNormalization(momentum=momentum)(x)
    return LeakyReLU(alpha=0.2)(x)


def discriminator(x_in, unused_conditioning, mode, weight_decay=2.5e-5, num_filters=64):
    del unused_conditioning
    is_training = (mode == tf.estimator.ModeKeys.TRAIN)

    x = discriminator_block(x_in, num_filters, batchnorm=False,  is_training = is_training)
    x = discriminator_block(x, num_filters, strides=2, is_training = is_training)

    x = discriminator_block(x, num_filters * 2,is_training = is_training)
    x = discriminator_block(x, num_filters * 2, strides=2, is_training = is_training)

    x = discriminator_block(x, num_filters * 4, is_training = is_training)
    x = discriminator_block(x, num_filters * 4, strides=2, is_training = is_training)

    x = discriminator_block(x, num_filters * 8, is_training = is_training)
    x = discriminator_block(x, num_filters * 8, strides=2, is_training = is_training)

    x = Flatten()(x)

    x = Dense(1024)(x)
    x = LeakyReLU(alpha=0.2)(x)
    x = Dense(1, activation='sigmoid')(x)

    # return Model(x_in, x)
    return x


