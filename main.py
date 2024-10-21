import time
import requests

import config as config

API_URL = "https://api.openai.com/v1/threads"
API_KEY = config.API_KEY
ID_ASSISTENT = config.ID_ASSISTENT

thread_id = None
run_id = None

call_id = None
function_arguments = None

def validar_thread(thread_id):
    if thread_id:
        return True
    else:
        return False

def criar_mensagem(pergunta):
    global thread_id
    url = f"{API_URL}/{thread_id}/messages"
    headers = get_headers()
    data = get_data_messagem(pergunta)
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
                    call_id = (
                        status_response.get('required_action') and
                        status_response['required_action'].get('submit_tool_outputs') and
                        status_response['required_action']['submit_tool_outputs'].get('tool_calls') and
                        len(status_response['required_action']['submit_tool_outputs']['tool_calls']) > 0 and
                        status_response['required_action']['submit_tool_outputs']['tool_calls'][0].get('id')
                    )
                        
                    global function_arguments
                    function_arguments = (
                        status_response.get('required_action') and
                        status_response['required_action'].get('submit_tool_outputs') and
                        status_response['required_action']['submit_tool_outputs'].get('tool_calls') and
                        len(status_response['required_action']['submit_tool_outputs']['tool_calls']) > 0 and
                        status_response['required_action']['submit_tool_outputs']['tool_calls'][0].get('function') and
                        status_response['required_action']['submit_tool_outputs']['tool_calls'][0]['function'].get('arguments')
                    )

                    if function_arguments:
                        print(function_arguments)
                        
                    aguardando_resposta = False
                elif run_status == "queued":
                    print("Execução na fila.")
                elif run_status == "in_progress":
                    print("Execução em andamento.")
                else:
                    print(f"Status desconhecido: {run_status}")

        
        
if __name__ == "__main__":
    main()
