import coremltools
import scipy
import torch
import torch.onnx
import os
import torchvision
import logging

from coremltools.models.neural_network import flexible_shape_utils

from models import MobileNetSkipAdd
import onnx
from onnx import version_converter
import onnx_coreml
import onnx.utils
import torch.jit
import PIL

INT_MAX = 2 ** 30

onnx_model_path = os.path.join('fastdepth.onnx')
onnx_fast_model_path = os.path.join('fastestdepth.onnx')
coreml_model_path = os.path.join('FastDepth.mlmodel')


def _convert_upsample(builder, node, graph, err):
    if 'scales' in node.attrs:
        scales = node.attrs['scales']
    elif len(node.input_tensors):
        scales = node.input_tensors[node.inputs[1]]
    else:
        # HACK: Manual scales
        # PROVIDE MANUAL SCALE HERE
        scales = [1, 1, 0.5, 0.5]

    scale_h = scales[2]
    scale_w = scales[3]
    input_shape = graph.shape_dict[node.inputs[0]]
    target_height = int(input_shape[-2] * scale_h)
    target_width = int(input_shape[-1] * scale_w)

    builder.add_resize_bilinear(
        name=node.name,
        input_name=node.inputs[0],
        output_name=node.outputs[0],
        target_height=target_height,
        target_width=target_width,
        mode='UPSAMPLE_MODE'
    )


def _convert_slice_v9(builder, node, graph, err):
    '''
    convert to CoreML Slice Static Layer:
    https://github.com/apple/coremltools/blob/655b3be5cc0d42c3c4fa49f0f0e4a93a26b3e492/mlmodel/format/NeuralNetwork.proto#L5082
    '''
    logging.warn(graph.shape_dict)

    data_shape = graph.shape_dict[node.inputs[0]]
    len_of_data = len(data_shape)
    begin_masks = [True] * len_of_data
    end_masks = [True] * len_of_data

    default_axes = list(range(len_of_data))
    default_steps = [1] * len_of_data

    ip_starts = node.attrs.get('starts')
    ip_ends = node.attrs.get('ends')
    axes = node.attrs.get('axes', default_axes)
    steps = node.attrs.get('steps', default_steps)

    starts = [0] * len_of_data
    ends = [0] * len_of_data

    for i in range(len(axes)):
        current_axes = axes[i]
        starts[current_axes] = ip_starts[i]
        ends[current_axes] = ip_ends[i]
        if ends[current_axes] != INT_MAX or ends[current_axes] < data_shape[current_axes]:
            end_masks[current_axes] = False

        if starts[current_axes] != 0:
            begin_masks[current_axes] = False

    builder.add_slice_static(
        name=node.name,
        input_name=node.inputs[0],
        output_name=node.outputs[0],
        begin_ids=starts,
        end_ids=ends,
        strides=steps,
        begin_masks=begin_masks,
        end_masks=end_masks
    )


# model = MobileNetSkipAdd((224, 224))
# model.eval()

checkpoint = torch.load(os.path.join('mobilenet-nnconv5dw-skipadd-pruned.pth.tar'),map_location=torch.device('cpu'))
start_epoch = checkpoint['epoch']
best_result = checkpoint['best_result']
model = checkpoint['model']
model.eval()
print("=> loaded best model (epoch {})".format(checkpoint['epoch']))

batch_size = 1
dummy_input = torch.randn((1, 3, 224, 224))

traced_script_module = torch.jit.trace(model, dummy_input)
traced_script_module.save("fastdepth.pt")

torch_out = torch.onnx.export(
    model=model,
    args=dummy_input,
    f=onnx_model_path,
    opset_version=9,
    verbose=True,
    do_constant_folding=False,
    input_names=['data'],
    output_names=['decode_conv6/2'],
    export_params=True,
    training=False,
    operator_export_type=torch.onnx.OperatorExportTypes.ONNX_ATEN_FALLBACK
)

onnx_model = onnx.load(onnx_model_path)
# onnx_model = version_converter.convert_version(onnx_model, target_version = 11)
# polished_model = onnx.utils.polish_model(onnx_model)
# print('The model is:\n{}'.format(onnx_model))
# onnx.checker.check_model(polished_model)
# print('The model is checked!')
# logging.warn(onnx_model.graph.shape_dict)
os.system("python3 -m onnxsim fastdepth.onnx fastestdepth.onnx")
onnx_faster_model = onnx.load(onnx_fast_model_path)
cml_model = onnx_coreml.convert(
    onnx_faster_model,
    preprocessing_args={'is_bgr': True, 'image_scale': 1.0/255.0},
    image_input_names=['data'],
    # image_output_names=['decode_conv6/2'],
    custom_conversion_functions={
        # "Slice": _convert_slice_v9,
        'Upsample': _convert_upsample
    },
    # disable_coreml_rank5_mapping=True
    target_ios='13'
)
cml_model.save(coreml_model_path)

# spec = coremltools.utils.load_spec(coreml_model_path)
# img_size_ranges = flexible_shape_utils.NeuralNetworkImageSizeRange()
# img_size_ranges.add_height_range((64, -1))
# img_size_ranges.add_width_range((64, -1))
# flexible_shape_utils.update_image_size_range(spec, feature_name='data', size_range=img_size_ranges)
# coremltools.models.utils.save_spec(spec, coreml_model_path)

exported_model = coremltools.models.MLModel(coreml_model_path)
exported_model.author = 'Fincher'
exported_model.short_description = 'Fast Depth'
exported_model.save(coreml_model_path)

rgba_image = PIL.Image.open("./test.png")
rgb_image = rgba_image.convert('RGB')
rgb_image.save('./test_converted.jpg')
predictions = exported_model.predict({'data': rgb_image})
print(predictions['decode_conv6/2'][0][0])
scipy.misc.toimage(predictions['decode_conv6/2'][0][0]).save('test_out.jpg')


spec = coremltools.utils.load_spec(coreml_model_path)
spec.description.input[0].type.imageType.colorSpace = coremltools.proto.FeatureTypes_pb2.ImageFeatureType.RGB
coremltools.utils.save_spec(spec, coreml_model_path)
