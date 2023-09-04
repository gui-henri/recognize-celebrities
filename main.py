import os
import argparse
import platform
import boto3
import requests
import base64
import json
from dotenv import load_dotenv

load_dotenv()

def signup(email, name, password):
    if name.strip() != "":
        print("Se esta for sua primeira vez logando, você precisa se cadastrar.")
        print("Deseja se cadastrar? (s/n)")
        if input() == 's':
            cognito = boto3.client('cognito-idp', region_name='us-east-1')
            try:
                response = cognito.sign_up(
                    ClientId=os.getenv('CLIENT_ID'),
                    Username=email,
                    Password=password,
                    UserAttributes=[
                        {
                            'Name': 'name',
                            'Value': name
                        },
                        {
                            'Name': 'email',
                            'Value': email
                        }
                    ]
                )
                response = cognito.confirm_sign_up(
                    ClientId=os.getenv('CLIENT_ID'),
                    Username=email,
                    ConfirmationCode=input("Digite o código de confirmação: ")
                )
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print("Usuário cadastrado com sucesso!")
                    return True
                else:
                    print("Erro ao cadastrar usuário.")
                    return False
            except Exception as e:
                raise Exception(e)
        else:
            print("Encerrando processo de cadastramento...")
            return False

def signin(username, password):
    cognito = boto3.client('cognito-idp', region_name='us-east-1')

    try:
        auth_response = cognito.initiate_auth(
            ClientId=os.getenv('CLIENT_ID'),
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        id_token = auth_response['AuthenticationResult']['IdToken']
        
        return id_token

    except Exception as e:
        print("Erro ao realizar login: {}".format(e))
        id_token = None

def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def get_args():
    parser = argparse.ArgumentParser(description='Reconhecimento de celebridades em imagens')
    parser.add_argument('--image', type=str, help='Caminho da imagem')
    args = parser.parse_args()
    return args

def idol_recognition_service(image_path):
    user_info = get_user()
    try:
        signup(user_info[0], user_info[1], user_info[2])
    except Exception as e:
        print("Erro ao realizar cadastro: {}".format(e))
        return
    try:
        id_token = signin(user_info[0], user_info[2])
    except Exception as e:
        print("Erro ao realizar login: {}".format(e))
        return

    if id_token:
        try:
            process(image_path, id_token)
        except Exception as e:
            print("Erro ao processar imagem: {}".format(e))
            return

def process(img_path, id_token):
    print("Processando...")
    api_url = "https://11pk8r0vuj.execute-api.us-east-1.amazonaws.com/prod"
    headers = {
        'felix': f'{id_token}'
    }

    with open(img_path, 'rb') as image:
        image_bytes = image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        data = {
            'image': image_base64
        }

        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            response_body = json.loads(response_json['body'])
            for celebrity in response_body['CelebrityFaces']:
                print("Celebridade: {}".format(celebrity['Name']))
                print("Expressão: {}".format(celebrity['Face']['Emotions'][0]['Type']))
                print("Link para a página da celebridade: {}".format(celebrity['Urls'][0]))
        else:
            print("Erro ao realizar chamada à API: {}".format(response.reason))


def get_user():
    def create_user():
        user_info = get_user_info()
        print("Deseja salvar as informações de login? (s/n)")
        if input() == 's':
            with open('user.txt', 'w') as file:
                file.write(user_info[0] + '\n')
                file.write(user_info[1] + '\n')
                file.write(user_info[2] + '\n')
        return user_info

    def get_user_info():
        email = input("Digite o seu email: ")
        name = input("Digite o seu nome (opcional caso queira apenas fazer login): ")
        password = input("Digite a senha: ")
        return email, name, password

    if os.path.isfile('user.txt'):
        with open('user.txt', 'r') as file:
            lines = file.readlines()
            if len(lines) >= 3:
                return lines[0].strip(), lines[1].strip(), lines[2].strip()
            else:
                user = create_user()
    else:
        user = create_user()
    return user
            

def main():
    args = get_args()
    image_path = args.image
    idol_recognition_service(image_path)
    

if __name__ == '__main__':
    main()