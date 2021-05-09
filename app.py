from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import pickle
import torch

app = Flask(__name__)

class DataDic(object):
    def __init__(self, answers):
        self.answers = answers #全部答案(含重複)
        self.answers_norepeat = sorted(list(set(answers))) # 不重複
        self.answers_types = len(self.answers_norepeat) # 總共多少類
        self.ans_list = [] # 用於查找id或是text的list
        self._make_dic() # 製作字典
    
    def _make_dic(self):
        for index_a,a in enumerate(self.answers_norepeat):
            if a != None:
                self.ans_list.append((index_a,a))

    def to_id(self,text):
        for ans_id,ans_text in self.ans_list:
            if text == ans_text:
                return ans_id

    def to_text(self,id):
        for ans_id,ans_text in self.ans_list:
            if id == ans_id:
                return ans_text

    @property
    def types(self):
        return self.answers_types
    
    @property
    def data(self):
        return self.answers

    def __len__(self):
        return len(self.answers)
def to_bert_ids(tokenizer,q_input):
    # 將文字輸入轉換成對應的id編號
    return tokenizer.build_inputs_with_special_tokens(tokenizer.convert_tokens_to_ids(tokenizer.tokenize(q_input)))
    
def use_model(config_file_path, model_file_path, vocab_file_path, num_labels):
    # 選擇模型並加載設定
  from albert.albert_zh import AlbertConfig, AlbertTokenizer, AlbertForSequenceClassification
  #from transformers import BertConfig, BertForSequenceClassification, BertTokenizer
  model_config, model_class, model_tokenizer = (AlbertConfig, AlbertForSequenceClassification, AlbertTokenizer)
  config = model_config.from_pretrained(config_file_path,num_labels = num_labels)
  model = model_class.from_pretrained(model_file_path, config=config)
  tokenizer = model_tokenizer.from_pretrained(vocab_file_path)
  return model, tokenizer

# Channel Access Token
line_bot_api = LineBotApi('xmsRTuBrr3LPocqZVgSCiS6QxaVU2+kLzPULMwTbKcyBERQb0guGbsAs7bH7nXqpj7UDrprTyfzrBgN/H5+2Pf+r/TPlnxWru1ADhzttyLvy0CwnagBsb1ExCcWwRp9mtTz1z8gnDnyo5u1E9mXofAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('076bd63002200ae855c82b1985d3f1c6')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    pkl_file = open(r'C:\Users\DELL\OneDrive\桌面\data_features.pkl', 'rb')
    data_features = pickle.load(pkl_file)
    answer_dic = data_features['answer_dic']
    model_setting = {
         "config_file_path":r"C:/Users/DELL/Desktop/trained_model4-20200611T160437Z-001/trained_model4/config.json", 
         "model_file_path":r"C:/Users/DELL/Desktop/trained_model4-20200611T160437Z-001/trained_model4/pytorch_model.bin", 
         "vocab_file_path":r"C:/Users\DELL\Documents/專題/line-bot-tutorial-master/line-bot-tutorial-master/albert-zh-for-pytorch-transformers-master/albert_tiny/vocab.txt",
         "num_labels":23 # 分幾類
     }
    model, tokenizer = use_model(**model_setting)
    model.eval()
    bert_ids = to_bert_ids(tokenizer,message)
    assert len(bert_ids) <= 512
    input_ids = torch.LongTensor(bert_ids).unsqueeze(0)
        # predict
    outputs = model(input_ids)
    predicts = outputs[:2]
    predicts = predicts[0]
    max_val = torch.max(predicts)
    label = (predicts == max_val).nonzero().numpy()[0][1]
    ans_label = answer_dic.to_text(label)
    line_bot_api.reply_message(event.reply_token, ans_label)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    #app.run(host='127.0.0.1', port=4040)
    app.debug = True
    #app.run()
