import os

import onnxruntime
import numpy as np
import PIL
import PIL.Image
from skimage.transform import resize
from skimage import io

onnx_fast_model_path = os.path.join('fastestdepth.onnx')
# onnx_faster_model = onnx.load(onnx_fast_model_path)


rgba_image = PIL.Image.open("./test.png")
rgb_image = rgba_image.convert('RGB')
rgb_image.save('./test_converted.jpg')

img = io.imread("./test.png")
img = np.rollaxis(img, 2, 0)
img224 = resize(img / 255, (3, 224, 224), anti_aliasing=True)
ximg = img224[np.newaxis, :, :, :]
ximg = ximg.astype(np.float32)
sess = onnxruntime.InferenceSession(onnx_fast_model_path)

input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[0].name
result = sess.run(None, {input_name: ximg})
prob = result[0]