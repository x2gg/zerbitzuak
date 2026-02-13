from typing import Optional
from fastapi import APIRouter, Request, Response, File, UploadFile, Body, HTTPException, Depends, Header
import requests
import os
from app.core.security import get_username_from_apisix_request, verify_file_size,validate_file_type,sanitize_filename
from app.services.user import UserService
from app.api.deps import get_user_service, get_current_user
from app.schemas.nlp import TextRequest
import time
from openai import OpenAI

router = APIRouter()
user_service = UserService(get_user_service)

NLP_URL = os.getenv('NLP_URL', 'http://lemma_eta_nerc:8010')
# NLP_URL = os.getenv('NLP_URL', 'http://lematizatzailea_eta_nerc:8010')

def api_key_header(apikey: str = Header(..., description="API key for authentication")):
    """
    Solo para documentación. No valida nada en FastAPI.
    """
    return apikey

# Function to call NLP Tools with text input
async def call_nlp_text(request: Request, nlp: str):
	try:
		
		resp = requests.request(
			method=request.method,
			#url=f"{NLP_URL}/api/{nlp}",
			url=f"{NLP_URL}/{nlp}",
			data=await request.body(),
			headers={k: v for k, v in request.headers.items() if k != "host"},
			params=request.query_params,
		)
		return Response(
			content=resp.content,
			status_code=resp.status_code,
			headers=resp.headers
		)
	except requests.exceptions.RequestException as e:
		raise HTTPException(status_code=500, detail=f"Error calling NLP tool: {str(e)}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error calling NLP tool: {str(e)}")

# Function to call NLP Tools with file input
async def call_nlp_file(request: Request, nlp: str, file_content: bytes, filename: str, content_type: str):
	try:        
		# Prepare the request to the NLP service
		files = {"file": (filename, file_content, content_type)}
		
		resp = requests.post(
			#url=f"{NLP_URL}/api/{nlp}",
			url=f"{NLP_URL}/{nlp}",
			files=files,
			headers={k: v for k, v in request.headers.items() 
				if k.lower() not in ["host", "content-length", "content-type"]},
			params=request.query_params,
		)
		
		return Response(
			content=resp.content,
			status_code=resp.status_code,
			headers=dict(resp.headers)
		)
	except requests.exceptions.RequestException as e:
		raise HTTPException(status_code=500, detail=f"Error calling NLP tool: {str(e)}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")



@router.post("/lemma", include_in_schema=False)
async def lemma_proxy(request: Request, payload: TextRequest = Body(...)): # , apikey: str = Depends(api_key_header)
	text = payload.text
	return await call_nlp_text(request, "lemma")

@router.post("/lemma_private")
async def lemma_private_proxy(request: Request, payload: TextRequest = Body(...), apikey: str = Depends(api_key_header)): # , apikey: str = Depends(api_key_header)
	text = payload.text
	return await call_nlp_text(request, "lemma")

@router.post("/lemma_file", include_in_schema=False)
async def lemma_file_proxy(request: Request, file: UploadFile = File(...)): #, apikey: str = Depends(api_key_header)
	try:
		original_filename, sanitized_filename = await sanitize_filename(file)
	except HTTPException as e:
		return HTTPException(status_code=400, detail="Invalid filename")
	
	try:
		valid_type = await validate_file_type(file)
	except HTTPException as e:
		return HTTPException(status_code=400, detail="File type not allowed")

	valid_size = await verify_file_size(file)
	if not valid_size:
		return HTTPException(status_code=413, detail="File too large")

	# Read file content after all validations
	file_content = await file.read()
	
	return await call_nlp_file(request, "lemma", file_content, sanitized_filename, file.content_type)


@router.post("/nerc", include_in_schema=False)
async def nerc_proxy(request: Request, payload: TextRequest = Body(...)): #, apikey: Optional[str] = Depends(api_key_header)
	text = payload.text
	return await call_nlp_text(request, "nerc")

@router.post("/nerc_private")
async def nerc_private_proxy(request: Request, payload: TextRequest = Body(...), apikey: Optional[str] = Depends(api_key_header)): #, apikey: Optional[str] = Depends(api_key_header)
	text = payload.text
	return await call_nlp_text(request, "nerc")

@router.post("/nerc_file", include_in_schema=False)
async def nerc_file_proxy(request: Request, file: UploadFile = File(...)): #, apikey: str = Depends(api_key_header)
	try:
		original_filename, sanitized_filename = await sanitize_filename(file)
	except HTTPException as e:
		return HTTPException(status_code=400, detail="Invalid filename")
	
	try:
		valid_type = await validate_file_type(file)
	except HTTPException as e:
		return HTTPException(status_code=400, detail="File type not allowed")

	valid_size = await verify_file_size(file)
	if not valid_size:
		return HTTPException(status_code=413, detail="File too large")

	# Read file content after all validations
	file_content = await file.read()
	
	return await call_nlp_file(request, "nerc", file_content, sanitized_filename, file.content_type)

	#from fastapi.openapi.docs import get_swagger_ui_html

	

# @router.post("/latxa_private_nlp")
# async def latxa_proxy(request: Request, payload: TextRequest = Body(...), apikey: str = Depends(api_key_header)): # , apikey: str = Depends(api_key_header)

# 	# Edo http://trumoi.ixa.eus:8002/v1
# 	client = OpenAI(base_url=f"http://158.227.114.118:8002/v1", api_key="EMPTY")

# 	LATXA_SYSTEM_PROMPT = (
# 		"You are a helpful Artificial Intelligence assistant called Latxa, "
# 		"created and developed by HiTZ, the Basque Center for Language Technology research center. "
# 		"The user will engage in a multi-round conversation with you, asking "
# 		"initial questions and following up with additional related questions. "
# 		#"Your goal is to provide thorough, relevant and insightful responses "
# 		"Your goal is to lemmatize and perform named entity recognition (NER)"
# 		#"to help the user with their queries. Every conversation will be "
# 		"to help the user with their queries. Every conversation will be "

# 		#"conducted in standard Basque, this is, the first question from the user will be "
# 		#"you should lemmatize and perform named entity recognition (NER) on the provided text. "
# 		"only json format  word:original word lema:lemma and ner:type_of_entity [PER, LOC, ORG, MISC] . Take in consideration the context of the sentences. "
# 		"more than one word can be part of the same entity. "
# 		# "in Basque, and you should respond in formal Basque as well. Conversations will "
# 		# "cover a wide range of topics, including but not limited to general "
# 		# "knowledge, science, technology, entertainment, coding, mathematics, "
# 		# "and more. Today is {date}."
# 	)

# 	def today():
# 		return time.strftime("%A %B %e, %Y", time.gmtime())

# 	messages = [
# 		{
# 			"role": "system",
# 			"content": LATXA_SYSTEM_PROMPT.format(date=today()),
# 		},
# 		{
# 			"role": "user",
# 			"content": payload.text,
# 		},
# 	]
	
# 	response = client.chat.completions.create(
# 		model="Latxa-Llama-3.1-70B-Instruct-exp_2_101",
# 		messages=messages,
# 		max_tokens=2048,
# 		temperature=0.9,
# 		top_p=0.95,
# 		# frequency_penalty=0.1,
# 	)
# 	return Response(
# 		content=response.choices[0].message.content,
# 		status_code=200,
# 		media_type="text/plain"
# 	)
# 	# print(response.choices[0].message.content)
# 	# """
# 	# > Egun on! Ondo nago, eskerrik asko galdetzeagatik. Zer moduz zaude zu? Zer gai interesatzen zaizu gaur eztabaidatzeko?
# 	# """

# @router.post("/latxa_private_translate")
# async def latxa_proxy(request: Request, payload: TextRequest = Body(...), apikey: str = Depends(api_key_header)): # , apikey: str = Depends(api_key_header)

# 	# Edo http://trumoi.ixa.eus:8002/v1
# 	client = OpenAI(base_url=f"http://158.227.114.118:8002/v1", api_key="EMPTY")

# 	LATXA_SYSTEM_PROMPT = (
# 			"**EARLY EXIT (runs BEFORE anything else)**"
# 			"1) First, classify <ORIGINAL>."
# 			"2) If it contains ANY of:"
# 			"   - Pornographic/explicit sexual content (incl. escorting)"
# 			"   - Online gambling/casino/betting"
# 			"   - Trading/crypto/forex promotional content"
# 			"   - Lists of unrelated keywords or phrases lacking complete sentences and grammatical connectors (SEO spam)"
# 			"THEN immediately output exactly:"
# 			"<TRANSLATION>CONTENT FLAG</TRANSLATION>"
# 			"and STOP — ignore all other instructions."
# 			"3) If not, proceed with translation rules."
# 			""
# 			"You are a professional translator from introduced text to BASQUE. Follow **all** instructions exactly."
# 			""
# 			"**Crucial Formatting Rules (READ CAREFULLY — HARD REQUIREMENTS):**"
# 			"1. **Preserve formatting EXACTLY.**"
# 			"* Do **not** add, remove, or modify any line breaks."
# 			"* You must output the **exact same number of lines** as the input."
# 			"* Each line in your output must correspond exactly to one line in the input."
# 			"* You must **never** insert additional blank lines that do not exist in the original text."
# 			"* Do **not** insert blank lines for readability."
# 			"2. **Translate every token.**"
# 			"Do not skip, summarize, or ignore any word, punctuation mark, or spacing."
# 			"3. **No literal translation.**"
# 			"Make the English natural and fluent, but **do not** change formatting."
# 			"4. **No hallucinations.**"
# 			"Do not add explanations, commentary, or any content that isn’t in the original."
# 			"5. **Output format**"
# 			"Enclose the translated text **only** in:"
# 			"<TRANSLATION>"
# 			"</TRANSLATION>"
# 			"Nothing before or after."
# 			"6. **If you cannot follow these formatting rules exactly, output:**"
# 			"`ERROR: formatting rule violated`"
# 			""
# 			"**Additional Strict Requirements:**"
# 			"- Do **NOT** insert extra whitespace."
# 			"- Do **NOT** auto-format paragraphs."
# 			"- Do **NOT** add blank lines."
# 			"- Do NOT reinterpret or restructure the text. Do NOT treat long lines as paragraphs. You must preserve every line exactly as written, even if the line is extremely long, contains many sentences, or appears to represent multiple paragraphs."
# 			"- Do NOT split any lines into multiple lines. Even if a line contains many sentences, you must keep it as a single line exactly as in the original."
# 			"- Treat every visible line break as unchangeable."
# 			"- When in doubt, copy the structure line by line."
# 			""
# 			"Remember the early exit rule before you consider translating."

# 	)

# 	def today():
# 		return time.strftime("%A %B %e, %Y", time.gmtime())

# 	messages = [
# 		{
# 			"role": "system",
# 			"content": LATXA_SYSTEM_PROMPT.format(date=today()),
# 		},
# 		{
# 			"role": "user",
# 			"content": payload.text,
# 		},
# 	]
	
# 	response = client.chat.completions.create(
# 		model="Latxa-Llama-3.1-70B-Instruct-exp_2_101",
# 		messages=messages,
# 		max_tokens=2048,
# 		temperature=0.9,
# 		top_p=0.95,
# 		# frequency_penalty=0.1,
# 	)
# 	return Response(
# 		content=response.choices[0].message.content,
# 		status_code=200,
# 		media_type="text/plain"
# 	)
# 	# print(response.choices[0].message.content)
# 	# """
# 	# > Egun on! Ondo nago, eskerrik asko galdetzeagatik. Zer moduz zaude zu? Zer gai interesatzen zaizu gaur eztabaidatzeko?
# 	# """
