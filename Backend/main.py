from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated,List,Literal,Optional
import json
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify ["http://localhost:8501"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Patient(BaseModel):
    
    id: Annotated[str, Field(..., description="Unique identifier for the patient", examples=["P001"])]
    name: Annotated[str, Field(..., description="Full name of the patient")]
    city: Annotated[str, Field(..., description="Current residing city of the patient")]
    age: Annotated[int, Field(..., description="Age of the patient in years", gt=0, lt=120)]
    gender: Annotated[Literal['male','female','other'], Field(..., description='gender of the patient')]
    height: Annotated[float, Field(..., description="Height of the patient in meters", gt=0)]
    weight: Annotated[float, Field(..., description="Weight of the patient in kilograms", gt=0)]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif 18.5 <= self.bmi < 25:
            return 'Normal weight'
        elif 25 <= self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'

class Patient_update(BaseModel):
    
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female','other']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
        

def load_data():
    with open('patients.json', 'r') as f:
        data=json.load(f)
    return data

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data,f, indent=4)


@app.get("/")
def hello():
    return {'message':'Patient Management System API'}

@app.get("/about")
def about():
    return {'message':'This is a Patient Management System API built with FastAPI'}

@app.get("/view")
def view():
    data=load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve", example="P001")):
    data=load_data()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description="sort on basis of height, weight or BMI"), order:str = Query('asc', description="asc or desc")):
    
    valid_fields=['height','weight','bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Must be one of {valid_fields}")
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400, detail="Invalid order. Must be 'asc' or 'desc'")
    
    data=load_data()
    sort_order=True if order=='desc' else False
    sorted_data=sorted(data.values(), key=lambda x:x.get(sort_by,0), reverse=sort_order)

    return sorted_data

@app.post('/create')
def create_patient(patient: Patient):
    # load existing data
    data=load_data()
    #check if patient with same id already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")
    # add new patient
    data[patient.id]=patient.model_dump()
    # save updated data
    save_data(data)
    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient_id": patient.id})

@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: Patient_update):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient=data[patient_id]
    updated_data=patient_update.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        existing_patient[key]=value
    
    #existing_patient['id']=patient_id
    existing_pydantic_obj=Patient(id=patient_id, **existing_patient)

    existing_patient=existing_pydantic_obj.model_dump()
    
    data[patient_id]=existing_patient
    save_data(data)
   
    return {"message": "Patient updated successfully"}
    
@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})