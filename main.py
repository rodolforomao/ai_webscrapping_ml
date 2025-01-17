import json
import time
import requests

import config as config
import openai as openai

API_URL = openai.API_URL
API_KEY = config.API_KEY
ID_ASSISTENT = config.ID_ASSISTENT

thread_id = None
run_id = None

call_id = None
function_arguments = None


def criar_mensagem(pergunta):
    global thread_id
    url = f"{API_URL}/{thread_id}/messages"
    headers = get_headers()
    data = get_data_messagem(pergunta)
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def submit_tool_outputs(pergunta):
    global thread_id
    global run_id
    url = f"{API_URL}/{thread_id}/runs/{run_id}/submit_tool_outputs"
    headers = get_headers()
    data = {
            "tool_outputs": [
                {
                    "tool_call_id": f"{call_id}",
                    "output": f"{pergunta}",
                }
            ]
        }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def criar_run():
    global thread_id
    url = f"{API_URL}/{thread_id}/runs"
    headers = get_headers()
    data = get_assistent_id()
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response = response.json()
        global run_id
        run_id = response.get("id")
    return response

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}"
        ,"OpenAI-Beta": "assistants=v2"
        }
    
def get_data_create_run(resposta):
    
    messages = get_data_messagem(resposta)
    assistent = get_assistent_id()
    return {
        "assistant_id": f"{ID_ASSISTENT}"
        ,"thread" :  {
            "messages": [
                messages
                ]
            }
    }
    
def get_assistent_id():
    return {
        "assistant_id": f"{ID_ASSISTENT}"
    }
    
def get_data_messagem(resposta):
    return {
                "role": "user",
                "content": f"{resposta}"
            }
    

    

    
def criar_mensagem_runs(resposta):
    url = f"{API_URL}/runs"
    headers = get_headers()
    data = get_data_create_run(resposta)
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response = response.json()
        global run_id
        global thread_id
        run_id = response['id']
        thread_id = response['thread_id']
    return response

def capturar_resposta(pergunta):
    resposta = input(pergunta)
    return resposta

def obter_status_run():
    url = f"{API_URL}/{thread_id}/runs/{run_id}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    return response.json()

def obter_resposta_mensagem():
    url = f"{API_URL}/{thread_id}/messages"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    return response.json()

def tratar_status(run_status):
    if run_status == "completed":
        print("Execução completada.")
    elif run_status == "required_action":
        print("Ação necessária.")
    elif run_status == "requires_action":
        print("Requer ação.")
    elif run_status == "queued":
        print("Execução na fila.")
    elif run_status == "in_progress":
        print("Execução em andamento.")
    else:
        print(f"Status desconhecido: {run_status}")

def search_mercado_livre(criteria):
    url = "https://api.mercadolibre.com/sites/MLB/search"
    descricao = criteria.get("criteria", {}).get("descricao")
    limite = criteria.get("criteria", {}).get("limite")
    if limite is None:
        limite = 5
    params = {
        "q": descricao,
        "limit": limite
    }
    return requests.get(url, params=params)

def main():
    global thread_id
    global run_id
        
    while True:
    
        pergunta = "Digite sua pergunta: "
        pergunta_usuario = capturar_resposta(pergunta)
        
        if thread_id is None and run_id  is None:
            status_response = criar_mensagem_runs(pergunta_usuario)
        else:
            # Cria mensagem e run
            criar_mensagem(pergunta_usuario)
            criar_run()
            
        aguardando_resposta = True
        
        while aguardando_resposta:
            time.sleep(.5)
            status_response = obter_status_run()
            if status_response:
                run_status = status_response['status']
                if run_status == "completed":
                    print("Execução completada.")
                    # pegar resposta e imprimir
                    resposta = obter_resposta_mensagem()
                    value = (
                        resposta.get("data") and 
                        resposta["data"][0].get("content") and 
                        resposta["data"][0]["content"][0].get("text") and 
                        resposta["data"][0]["content"][0]["text"].get("value")
                    )

                    if value != pergunta_usuario:
                        if value is not None:
                            print(value)
                            aguardando_resposta = False
                        else:
                            print('O valor não está disponível, aguardando um pouco mais.')
                    else:
                        print('O valor não está disponível, aguardando um pouco mais.')
                    
                elif run_status == "required_action":
                    print("Ação necessária.")
                    # chamar make
                    aguardando_resposta = False
                elif run_status == "requires_action":
                    print("Requer ação.")
                    
                    global call_id
                    call_id = get_call_id(status_response)
                        
                    global function_arguments
                    function_arguments = get_function_arguments(status_response)

                    if function_arguments:
                        print(function_arguments)
                    
                    resposta = search_mercado_livre(json.loads(function_arguments))
                    
                    response_content = resposta.content
                    
                    response_content = json.loads(response_content)

                    # Criando um array com as propriedades desejadas
                    products_array = [
                        {
                            "title": product["title"],
                            "price": product["price"],
                            "permalink": product["permalink"]
                        }
                        for product in response_content["results"]
                    ]
                    
                    products_text = "\n".join(
                        f"{product['title']};{product['price']};{product['permalink']}" for product in products_array
                    )
                    
                    response = submit_tool_outputs(products_text)
                    
                elif run_status == "queued":
                    print("Execução na fila.")
                elif run_status == "in_progress":
                    print("Execução em andamento.")
                else:
                    print(f"Status desconhecido: {run_status}")

        
def get_function_arguments(status_response):
    # Arguments: data.required_action.submit_tool_outputs.tool_calls[0].function.arguments


    return  (
                        status_response.get('required_action') and
                        status_response['required_action'].get('submit_tool_outputs') and
                        status_response['required_action']['submit_tool_outputs'].get('tool_calls') and
                        len(status_response['required_action']['submit_tool_outputs']['tool_calls']) > 0 and
                        status_response['required_action']['submit_tool_outputs']['tool_calls'][0].get('function') and
                        status_response['required_action']['submit_tool_outputs']['tool_calls'][0]['function'].get('arguments')
                     )
def get_call_id(status_response):
    # Call id: data.required_action.submit_tool_outputs.tool_calls[0].id


    return  (
                status_response.get('required_action') and
                status_response['required_action'].get('submit_tool_outputs') and
                status_response['required_action']['submit_tool_outputs'].get('tool_calls') and
                len(status_response['required_action']['submit_tool_outputs']['tool_calls']) > 0 and
                status_response['required_action']['submit_tool_outputs']['tool_calls'][0].get('id')
            )

if __name__ == "__main__":
    main()
