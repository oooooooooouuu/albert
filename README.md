# albert
訓練albert模型製作醫療問答聊天機器人  

sele.py:從台灣E院網站爬蟲，蒐集醫療問答集  
albert.py:負責將資料做簡單的清洗以及模型訓練以及儲存  
訓練程式碼部分參考於https://github.com/p208p2002/taipei-QA-BERT  
app.py:結合linebot，對用戶輸入的問題調用訓練完成的模型預測回答  
linebot需先在linedeveloper網站登入帳號建立provider  
更改app.py中的金鑰  
用ngrok建立網址，將https開頭的網址貼在provider WebhookURL(網址後面記得加/callback)
