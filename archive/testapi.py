# TODO(developer): Vertex AI SDK - uncomment below & run
#pip3 install --upgrade --user google-cloud-aiplatform
#gcloud auth application-default login

import vertexai
from vertexai.preview.generative_models import GenerativeModel

gemini_pro_model = GenerativeModel("gemini-pro")
model_response = gemini_pro_model.generate_content("What does the name Siavash means?")
print("model_response\n",model_response)

