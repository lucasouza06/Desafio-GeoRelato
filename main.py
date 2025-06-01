import typer 
import json
from datetime import datetime
from typing import Dict, List
from geopy.distance import geodesic

app = typer.Typer()

#  Classe Relator (Pessoa que faz o relato)
class Relator:
    def __init__(self, nome: str, documento: str, email: str, telefone: str, localizacao: tuple):
        self.nome = nome
        self.documento = documento
        self.email = email
        self.telefone = telefone
        self.localizacao = localizacao  # (lat, long)

#  Classe Relato (Informações sobre a catástrofe)
class Relato:
    def __init__(self, tipo: str, descricao: str, data: str, hora: str, localizacao: tuple, relator: Relator = None):
        self.tipo = tipo
        self.descricao = descricao
        self.data = data
        self.hora = hora
        self.localizacao = localizacao  # (lat, long)
        self.relator = relator

#  Função para validar se relato está dentro do raio permitido
def esta_dentro_do_raio(local_relato: tuple, ponto_central: tuple, raio_km=10) -> bool:
    distancia = geodesic(local_relato, ponto_central).km
    return distancia <= raio_km

#  Classe SistemaCadastro (Gerenciamento dos relatos)
class SistemaCadastro:
    def __init__(self, ponto_central: tuple, arquivo_json="dados.json", arquivo_relatores="relatores.json"):
        self.ponto_central = ponto_central
        self.arquivo_json = arquivo_json
        self.arquivo_relatores = arquivo_relatores

        #  Lista para armazenar os relatos
        # Permite fácil inserção, ordenação e filtragem por tipo, data ou localização.
        self.relatos = self.carregar_dados()

        # Dicionário para armazenar relatores com o documento como chave
        # Permite acesso rápido (O(1)) para evitar duplicatas e localizar relatores facilmente.
        self.relatores = self.carregar_relatores()

    def salvar_relatores(self):
        """Salva os relatores em um arquivo JSON."""
        with open(self.arquivo_relatores, "w") as f:
            json.dump({doc: relator.__dict__ for doc, relator in self.relatores.items()}, f, indent=4)
        print("💾 Relatores salvos com sucesso!")

    def carregar_relatores(self):
        """Carrega os relatores de um arquivo JSON corretamente."""
        try:
            with open(self.arquivo_relatores, "r") as f:
                dados = json.load(f)
                return {doc: Relator(**info) for doc, info in dados.items()} if dados else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def salvar_dados(self):
        """Salva os relatos em um arquivo JSON garantindo que os objetos sejam serializáveis."""
        with open(self.arquivo_json, "w") as f:
            json.dump([{
                "tipo": relato.tipo,
                "descricao": relato.descricao,
                "data": relato.data,
                "hora": relato.hora,
                "localizacao": relato.localizacao,
                "relator": {
                    "nome": relato.relator.nome,
                    "documento": relato.relator.documento,
                    "email": relato.relator.email,
                    "telefone": relato.relator.telefone,
                    "localizacao": relato.relator.localizacao
                } if relato.relator else None
            } for relato in self.relatos], f, indent=4)
        
        print("💾 Relatos salvos com sucesso!")

    def carregar_dados(self):
        """Carrega os relatos de um arquivo JSON."""
        try:
            with open(self.arquivo_json, "r") as f:
                dados_json = json.load(f)
                relatos = []
                for dados in dados_json:
                    relator_dados = dados.get("relator")
                    relator = Relator(**relator_dados) if relator_dados else None
                    relatos.append(Relato(
                        tipo=dados["tipo"],
                        descricao=dados["descricao"],
                        data=dados["data"],
                        hora=dados["hora"],
                        localizacao=tuple(dados["localizacao"]),
                        relator=relator
                    ))
                return relatos
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def registrar_relato(self, relato: Relato):
        if esta_dentro_do_raio(relato.localizacao, self.ponto_central):
            self.relatos.append(relato)
            self.salvar_dados()
            print("✅ Relato cadastrado com sucesso!")
        else:
            print("❌ O relato está fora do raio permitido.")

    def buscar_por_tipo(self, tipo: str) -> List[Relato]:
        return [relato for relato in self.relatos if relato.tipo.lower() == tipo.lower()]

    def buscar_por_periodo(self, data_inicio: str, data_fim: str) -> List[Relato]:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        return [relato for relato in self.relatos if data_inicio_dt <= datetime.strptime(relato.data, "%Y-%m-%d") <= data_fim_dt]
    
    def buscar_por_localizacao(self, localizacao_ref: tuple, raio_km: int) -> List[Relato]:
        return [relato for relato in self.relatos if esta_dentro_do_raio(relato.localizacao, localizacao_ref, raio_km)]

#  Função para exibir relatos organizadamente, verificando se o relator existe
def exibir_relato(relato: Relato):
    print("\n🔹 Relato Registrado 🔹")
    print(f"📌 Tipo: {relato.tipo}")
    print(f"📝 Descrição: {relato.descricao}")
    print(f"📅 Data: {relato.data} ⏰ Hora: {relato.hora}")
    print(f"📍 Localização: {relato.localizacao}")

    if isinstance(relato.relator, Relator):
        print(f"👤 Relator: {relato.relator.nome}")
    else:
        print("⚠️ Relator não encontrado!")

    print("=" * 40)

#  Inicializando o sistema com um ponto central fixo
sistema = SistemaCadastro(ponto_central=(-23.55, -46.63))

#  Comandos CLI
@app.command()
def adicionar_relator(nome: str, documento: str, email: str, telefone: str, lat: str, long: str):
    """Registra um relator no sistema, garantindo que não seja duplicado."""
    lat, long = float(lat), float(long)

    if documento in sistema.relatores:
        print(f"⚠️ Relator {nome} já está cadastrado com o documento {documento}.")
        return

    relator = Relator(nome, documento, email, telefone, (lat, long))
    sistema.relatores[documento] = relator
    sistema.salvar_relatores()
    print(f"✅ Relator {nome} cadastrado com sucesso!")

@app.command()
def adicionar_relato(tipo: str, descricao: str, data: str, hora: str, lat: str, long: str, documento_relator: str):
    """Registra um novo relato de catástrofe."""
    lat, long = float(lat), float(long)

    relator = sistema.relatores.get(documento_relator)
    if not relator:
        print(f"❌ Relator com documento '{documento_relator}' não encontrado!")
        return

    relato = Relato(tipo, descricao, data, hora, (lat, long), relator)
    sistema.registrar_relato(relato)

@app.command()
def buscar_por_tipo(tipo: str):
    """Busca relatos por tipo."""
    resultado = sistema.buscar_por_tipo(tipo)
    for relato in resultado:
        exibir_relato(relato)

@app.command()
def buscar_por_periodo(data_inicio: str, data_fim: str):
    """Busca relatos por período."""
    resultado = sistema.buscar_por_periodo(data_inicio, data_fim)
    for relato in resultado:
        exibir_relato(relato)

@app.command()
def buscar_por_localizacao(lat: float, long: float, raio_km: int):
    """Busca relatos por localização."""
    resultado = sistema.buscar_por_localizacao((lat, long), raio_km)
    for relato in resultado:
        exibir_relato(relato)

if __name__ == "__main__":
    app()
