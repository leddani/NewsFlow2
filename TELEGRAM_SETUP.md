# 🤖 Konfigurimi i Telegram Bot-it për NewsFlow AI Editor

Ky udhëzues ju tregon si të konfiguroni Telegram bot-in për NewsFlow AI Editor.

## 📋 Hapat e Konfigurimit

### 1. Krijimi i Bot-it në Telegram

1. **Hapni Telegram** dhe kërkoni për `@BotFather`
2. **Dërgoni komandën** `/newbot`
3. **Jepni një emër** për bot-in tuaj (p.sh. "NewsFlow AI Editor")
4. **Jepni një username** që përfundon me "bot" (p.sh. "newsflow_ai_editor_bot")
5. **Ruani token-in** që ju jep BotFather

### 2. Krijimi i Channel-it

1. **Krijoni një channel** në Telegram
2. **Shtoni bot-in** si administrator në channel
3. **Jepni të drejta** për të dërguar mesazhe
4. **Ruani username-in** e channel-it (p.sh. "@newsflow_reviews")

### 3. Gjetja e User ID

1. **Dërgoni një mesazh** bot-it tuaj
2. **Vizitoni URL-në**: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. **Gjeni user ID** tuaj në përgjigjen JSON

### 4. Konfigurimi i Variablave të Mjedisit

Krijoni një file `.env` në rrënjën e projektit:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_username
TELEGRAM_ADMIN_USER_ID=your_user_id_here

# OpenRouter Configuration
OPENROUTER_API_KEY=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

# Database Configuration
DATABASE_URL=sqlite:///./newsflow.db
```

## 🚀 Startimi i Bot-it

### Metoda 1: Nga API (Recomended)

1. **Startoni backend-in**:
   ```bash
   uvicorn newsflow_backend.main:app --reload
   ```

2. **Startoni bot-in** nga API:
   ```bash
   curl -X POST http://127.0.0.1:8000/telegram/start
   ```

3. **Kontrolloni statusin**:
   ```bash
   curl http://127.0.0.1:8000/telegram/status
   ```

### Metoda 2: Script i Pavarur

```bash
python run_telegram_bot.py
```

## 📱 Funksionalitetet e Bot-it

### Komandat e Disponueshme

- `/start` - Fillo bot-in dhe shfaq mesazhin e mirëseardhjes
- `/help` - Shfaq ndihmën për komandat
- `/status` - Kontrollo statusin e bot-it

### Butonat për Artikujt

Kur një artikull dërgohet për review, bot-i shfaq këto butona:

- **✅ Aprovo** - Aprovo artikullin për publikim
- **❌ Refuzo** - Refuzo artikullin
- **✏️ Edito** - Kërko redaktim të artikullit
- **📝 Detaje** - Shfaq më shumë informacion

## 🔧 Troubleshooting

### Problemi: "Bot token not configured"
**Zgjidhja**: Kontrolloni që `TELEGRAM_BOT_TOKEN` është vendosur në file-in `.env`

### Problemi: "Channel not found"
**Zgjidhja**: 
1. Kontrolloni që bot-i është administrator në channel
2. Kontrolloni që `TELEGRAM_CHANNEL_ID` është i saktë

### Problemi: "Forbidden: bot was blocked by the user"
**Zgjidhja**: 
1. Bllokoni dhe zbllokoni bot-in
2. Kontrolloni që bot-i ka të drejta të mjaftueshme

### Problemi: "Bot can't send messages to this chat"
**Zgjidhja**: 
1. Shtoni bot-in si administrator në channel
2. Jepni të drejta për të dërguar mesazhe

## 📊 Monitoring

### Kontrolli i Statusit

```bash
# Kontrollo statusin e bot-it
curl http://127.0.0.1:8000/telegram/status

# Përgjigja:
{
  "bot_initialized": true,
  "articles_in_cache": 5,
  "status": "running"
}
```

### Logs

Bot-i shfaq logs në console për:
- Inicializimin e bot-it
- Dërgimin e artikujve
- Veprimet e përdoruesve (aprovim/refuzim)
- Gabimet

## 🔒 Siguria

- **Mos ndani token-in** e bot-it publikisht
- **Përdorni .env** për variablat e ndjeshëm
- **Kontrolloni të drejtat** e bot-it në channel
- **Përdorni HTTPS** në production

## 📞 Ndihmë

Nëse keni probleme:

1. Kontrolloni logs në console
2. Verifikoni konfigurimin e variablave
3. Testoni bot-in me `/start` dhe `/help`
4. Kontrolloni që bot-i është administrator në channel

---

**🎉 Tani bot-i juaj është gati për të marrë artikuj për review!** 