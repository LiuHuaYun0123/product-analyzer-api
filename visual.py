import os
from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

# Set the values of your computer vision endpoint and computer vision key
# as environment variables:
try:
    endpoint = "https://visual-api.cognitiveservices.azure.com/"
    key = "53QRVR5IwtoPdN2CtJ6mfKWglqQleXmCa4Dsk4W57sfkCKabmcZxJQQJ99BFACi0881XJ3w3AAAEACOGNTnf"
except KeyError:
    print("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'")
    print("Set them before running this sample.")
    exit()

# Create an Image Analysis client for synchronous operations,
# using API key authentication
client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)
# Load image to analyze into a 'bytes' object
with open("01.jpg", "rb") as f:
    image_data = f.read()

# Get a caption for the image. This will be a synchronously (blocking) call.
result = client.analyze(
    image_data=image_data,
    visual_features=[VisualFeatures.CAPTION],
    gender_neutral_caption=True,  # Optional (default is False)
)

# Print caption results to the console
print("Image analysis results:")
print(" Caption:")
if result.caption is not None:
    print(f"   '{result.caption.text}', Confidence {result.caption.confidence:.4f}")

