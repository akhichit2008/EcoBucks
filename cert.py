import cv2
import numpy as np

def create_certificate(user_name):
    # Load the certificate template
    cert_image = cv2.imread("static/cert-template.png")
    
    # Define the font and size
    font = cv2.FONT_HERSHEY_DUPLEX
    font_size = 3  # Adjust this value to make the text bigger
    text = user_name
    
    # Calculate the text size and position to center it
    text_size = cv2.getTextSize(text, font, font_size, 2)[0]
    text_width, text_height = text_size
    x = (cert_image.shape[1] - text_width) // 2
    y = (cert_image.shape[0] + text_height) // 2

    # Add the text to the image
    cv2.putText(cert_image, text, (x, y), font, font_size, (0, 0, 0), 2)

    # Save the image
    cv2.imwrite(f"certificate_for_{user_name}.png", cert_image)

user_name = input("Enter the name: ")
create_certificate(user_name)
