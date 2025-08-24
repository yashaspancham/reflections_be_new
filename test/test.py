import cv2
import numpy as np

def resize_image(input_bytes, width, height):
    # Convert bytes to numpy array
    nparr = np.frombuffer(input_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Resize image
    resized_img = cv2.resize(img, (width, height))
    # Encode image back to bytes
    _, buffer = cv2.imencode('.jpg', resized_img)
    return buffer.tobytes()

#reading image and converting to bytes
data={"iamge_path":"./test_images/pexels-lina-1741205.jpg"}
f=open(data["iamge_path"],"rb")
image_bytes= f.read()
f.close()

#call the reszie function
resized_bytes=resize_image(image_bytes,1000,1000)

#save the image
image_out=open("./result_images/op_pexels-lina-1741205.jpg","wb")
image_out.write(resized_bytes)
image_out.close
