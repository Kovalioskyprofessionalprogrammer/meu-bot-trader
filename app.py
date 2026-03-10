import streamlit as st
import pandas as pd
import ccxt
import pandas_ta as ta
import plotly.graph_objects as go
import requests

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="AI Trader Dashboard Pro", layout="wide")

# --- FUNÇÃO DE ENVIO (ZAP / TELEGRAM) ---
# Explique ao professor: "Esta função é o Webhook que integra a IA com mensageiros externos"
def disparar_alerta(mensagem, plataforma="Telegram"):
    # Exemplo de lógica para Zap (via API genérica) ou Telegram
    if plataforma == "Telegram":
        token = "SEU_TOKEN"
        chat_id = "SEU_ID"
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={mensagem}"
        try: requests.get(url) 
        except: pass
    else:
        # Aqui entraria a URL da API do WhatsApp (ex: Twilio ou Evolution)
        st.info(f"Simulando envio para WhatsApp: {mensagem}")

# --- MOTOR DE INTELIGÊNCIA ---
def processar_ia(moeda, timeframe):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(moeda, timeframe=timeframe, limit=100)
    df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    
    # Indicadores Técnicos
    df['ma20'] = ta.sma(df['close'], length=20)
    
    ultimo = df.iloc[-1]
    corpo = abs(ultimo['open'] - ultimo['close'])
    sombra_sup = ultimo['high'] - max(ultimo['open'], ultimo['close'])
    
    # Lógica de Decisão Híbrida
    tendencia = "ALTA 📈" if ultimo['close'] > ultimo['ma20'] else "BAIXA 📉"
    sinal = "AGUARDAR ⏳"
    
    # Critério de entrada: Tendência de baixa + Estrela Cadente
    if tendencia == "BAIXA 📉" and sombra_sup > (corpo * 2):
        sinal = "VENDA (Estrela Cadente) 🎯"
        
    return df, tendencia, sinal, ultimo['close']

# --- FRONT-END DASHBOARD ---
st.title("🚀 Sistema Integrado de Trade IA")
st.markdown("---")

# Sidebar com Top 10 Moedas
lista_moedas = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'ADA/USDT',
    'XRP/USDT', 'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'DOGE/USDT'
]

with st.sidebar:
    st.header("⚙️ Parâmetros")
    moeda_sel = st.selectbox("Ativo (Top 10)", lista_moedas)
    tempo = st.selectbox("Timeframe", ['15m', '1h', '4h', '1d'])
    st.write("A IA analisa Price Action + Médias Móveis.")

try:
    df, tend, msg_sinal, preco_atual = processar_ia(moeda_sel, tempo)
    
    # Painel de Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Preço Atual", f"$ {preco_atual:.2f}")
    col2.metric("Tendência", tend)
    col3.metric("Sinal IA", msg_sinal)

    # Botões de Integração
    c1, c2 = st.columns(2)
    if c1.button("📩 Enviar Sinal para o Zap"):
        disparar_alerta(f"IA Alerta: {moeda_sel} gerou sinal de {msg_sinal}", plataforma="WhatsApp")
        st.success("Comando de envio para WhatsApp processado!")
    
    if c2.button("✈️ Enviar para Telegram"):
        disparar_alerta(f"IA Alerta: {moeda_sel} em tendência de {tend}")
        st.toast("Mensagem enviada ao bot!")

    # Gráfico Profissional
    fig = go.Figure(data=[go.Candlestick(
        x=df['ts'], open=df['open'], high=df['high'], 
        low=df['low'], close=df['close'], name="Preço"
    )])
    fig.add_trace(go.Scatter(x=df['ts'], y=df['ma20'], name="Média 20", line=dict(color='orange', width=2)))
    
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"Análise Técnica: {moeda_sel}")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro na conexão com os dados: {e}")
