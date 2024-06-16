from fastapi import status, HTTPException, APIRouter
from .. import schemas
from ..llm_service import LLMService

# To load the tensorflow model
from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
import tensorflow as tf
from ..cnn_service import CNNService

router = APIRouter()

cnn_service = CNNService()
cnn_service.load_models()

router = APIRouter(prefix="/query", tags=["query"])
llm_service = LLMService()

@router.post("/message", status_code=status.HTTP_201_CREATED)
def chat(query: schemas.Query):
    similar_docs = llm_service.vector_search(query.query)
    template = llm_service.get_prompt_template()
    formatted_template = template.format(similar_docs=similar_docs, query=query.query)  
    result = llm_service.get_mistral(formatted_template)
    return {"output": result}

@router.post("/classify_xray")
async def classify_xray(file: UploadFile = File(...)):
    contents = await file.read()
    image = tf.image.decode_image(contents, channels=3)
    predictions = cnn_service.classify_xray(image)
    labels = ['Cardiomegaly', 'Emphysema', 'Effusion', 'Hernia', 'Infiltration', 'Mass', 'Nodule', 'Atelectasis', 'Pneumothorax', 'Pleural_Thickening', 'Pneumonia', 'Fibrosis', 'Edema', 'Consolidation']
    result = {label: float(pred) for label, pred in zip(labels, predictions[0])}
    return JSONResponse(content=result)

@router.post("/select/{template_name}", status_code=status.HTTP_200_OK)
def select_template(template_name: str):
    try:
        llm_service.change_prompt_template(template_name)
        return {"message": f"Prompt template changed to {template_name}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))