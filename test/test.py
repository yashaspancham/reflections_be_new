from PIL import Image



data = {
    "image_path": "./test_images/pexels-lina-1741205.jpg",
    "output_path": "./result_images/output_pexels-lina-1741205.jpg",
}


def resize_image_keep_aspect(input_path, output_path, max_width, max_height):
    with Image.open(input_path) as img:
        img.thumbnail((max_width, max_height))
        img.save(output_path)

resize_image_keep_aspect(data["image_path"],data["output_path"],200,200)