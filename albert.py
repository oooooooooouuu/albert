# -*- coding: utf-8 -*-
"""albert.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wsMc5kDcxZubLyY-vlwQCLmlLZjBVSd4
"""

from google.colab import drive
drive.mount('/content/drive/')

import pandas as pd
import csv
df = pd.read_csv(r'/content/drive/My Drive/Colab Notebooks/data.csv')

def clean_df(df):
  for i in range(len(df['title'])):
    if type(df['title'][i]) != str:
      df = df.drop(index = [i])
  df.reset_index(drop=True, inplace=True)
  return df
df = clean_df(df)

def add_label(df):
  import re
  question = list(df['title'])
  answer = list(df['division'])
  for i in range(len(answer)):
    answer[i] = re.sub(r"\s+", "", answer[i])
  division_to_label = dict()
  s = ''
  k = 0
  for i in answer:
    if s != i:
      s = i
      division_to_label[i] = k
      k = k + 1
  assert len(question) == len(answer)
  #print(division_to_label)
  labels = []
  for i in answer:
    labels.append(division_to_label[i])
  df['label'] = labels
  #print(df.head())
  num_labels = len(division_to_label)
  #print(num_labels)
  return df, division_to_label, num_labels
df, division_to_label, num_labels = add_label(df)

import tensorflow as tf
device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

!git clone https://github.com/p208p2002/albert-zh-for-pytorch-transformers.git albert
!pip install boto3
model_setting = { 
        "config_file_path":"albert/albert_tiny/config.json", 
        "model_file_path":"albert/albert_tiny/pytorch_model.bin", 
        "vocab_file_path":"albert/albert_tiny/vocab.txt",
        "num_labels":num_labels # 分幾類
    }   
def use_model(config_file_path, model_file_path, vocab_file_path, num_labels):
    # 選擇模型並加載設定
  from albert.albert_zh import AlbertConfig, AlbertTokenizer, AlbertForSequenceClassification

  model_config, model_class, model_tokenizer = (AlbertConfig, AlbertForSequenceClassification, AlbertTokenizer)
  config = model_config.from_pretrained(config_file_path,num_labels = num_labels)
  model = model_class.from_pretrained(model_file_path, config=config)
  tokenizer = model_tokenizer.from_pretrained(vocab_file_path)
  return model, tokenizer
model, tokenizer = use_model(**model_setting)

from sklearn.model_selection import StratifiedShuffleSplit
def to_bert_ids(tokenizer,q_input):
  # 將文字輸入轉換成對應的id編號
  return tokenizer.build_inputs_with_special_tokens(tokenizer.convert_tokens_to_ids(tokenizer.tokenize(q_input)))
def split(df):
  q = df['title'].tolist()
  y = df['division'].tolist()
  skf = StratifiedShuffleSplit(n_splits=5)
  for train_index, test_index in skf.split(q, y):
    q_train = [q[index] for index in train_index]
    y_train = [y[index] for index in train_index]
    q_test = [q[index] for index in test_index]
    y_test = [y[index] for index in test_index]
  assert len(q_train) == len(y_train) and len(q_test) == len(y_test)
  train = []
  test = []
  for i in range(len(q_train)):
    train.append([q_train[i], y_train[i]])
  for i in range(len(q_test)):
    test.append([q_test[i], y_test[i]])
  df_train = pd.DataFrame(train, columns = ["question", "division"])
  df_test = pd.DataFrame(test, columns = ["question", "division"])
  return df_train, df_test

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

def convert_data_to_feature(tokenizer, df):
  df = df.dropna()
  question = []
  division = []
  for i in df['question']:
    q = i.strip()
    question.append(q)
  for i in df['division']:
    #d = i.strip()
    division.append(i)
  assert len(division) == len(question)
  q_tokens = []
  a_labels = []
  max_seq_len = 0
  division_dic = DataDic(division)
  question_dic = DataDic(question)
  for q in range(len(division)):
    bert_ids = to_bert_ids(tokenizer, question[q])
    if len(bert_ids) > 512:
      continue
    if(len(bert_ids)>max_seq_len):
      max_seq_len = len(bert_ids)
    q_tokens.append(bert_ids)
    a_labels.append(division_dic.to_id(division[q]))
  print('最長問句:', max_seq_len)
  assert max_seq_len <= 512
  original_length = []
  for q in q_tokens:
    length = len(q)
    original_length.append(length)
    while len(q)<max_seq_len:
      q.append(0)
  answer_labels = a_labels
  input_ids = q_tokens
  input_masks = []                                                                # position_ids:1代表是真實的單詞id，0代表補全位
  for i in range(len(q_tokens)):
    position_ids = []
    for j in range(original_length[i]):
        position_ids.append(1)
    while len(position_ids)<max_seq_len:
        position_ids.append(0)
    input_masks.append(position_ids)
  input_segment_ids = [[0]*max_seq_len for i in range(len(q_tokens))]
  assert len(input_ids) == len(q_tokens) and len(input_ids) == len(input_masks) and len(input_ids) == len(input_segment_ids)
  data_features = {'input_ids':input_ids,
                    'input_masks':input_masks,
                    'input_segment_ids':input_segment_ids,
                    'answer_labels':answer_labels,
                    'question_dic':question_dic,
                    'answer_dic':division_dic}
  output = open(r'/content/drive/My Drive/Colab Notebooks/trained_model/data_features.pkl', 'wb')
  pickle.dump(data_features,output)
  return data_features

from torch.utils.data import TensorDataset
from torch.utils.data import DataLoader
def make_dataset(input_ids, input_masks, input_segment_ids, answer_lables):
    all_input_ids = torch.tensor([input_id for input_id in input_ids], dtype=torch.long)
    all_input_masks = torch.tensor([input_mask for input_mask in input_masks], dtype=torch.long)
    all_input_segment_ids = torch.tensor([input_segment_id for input_segment_id in input_segment_ids], dtype=torch.long)
    all_answer_lables = torch.tensor([answer_lable for answer_lable in answer_lables], dtype=torch.long)
    return TensorDataset(all_input_ids, all_input_masks, all_input_segment_ids, all_answer_lables)

import torch
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
print("using device",device)
model.to(device)

def compute_accuracy(y_pred, y_target):
    # 計算正確率
    _, y_pred_indices = y_pred.max(dim=1)
    n_correct = torch.eq(y_pred_indices, y_target).sum().item()
    return n_correct / len(y_pred_indices) * 100

!pip install transformers
from transformers import get_linear_schedule_with_warmup
from transformers import AdamW
no_decay = ['bias', 'LayerNorm.weight']
optimizer_grouped_parameters = [
        {'params': [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)], 'weight_decay': 0.0},
        {'params': [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
        ]
optimizer = AdamW(optimizer_grouped_parameters, lr=1e-4, eps=1e-8)
# scheduler = WarmupLinearSchedule(optimizer, warmup_steps=args.warmup_steps, t_total=t_total)
#scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=30, num_training_steps=507)
model.zero_grad()

import pickle

for epoch in range(30):
  df_train, df_test = split(df)

  data_feature_train = convert_data_to_feature(tokenizer, df_train)
  input_ids = data_feature_train['input_ids']
  input_masks = data_feature_train['input_masks']
  input_segment_ids = data_feature_train['input_segment_ids']
  answer_labels = data_feature_train['answer_labels']
  train_dataset = make_dataset(input_ids = input_ids, input_masks = input_masks, input_segment_ids = input_segment_ids, answer_lables = answer_labels)

  data_feature_test = convert_data_to_feature(tokenizer, df_test)
  input_ids = data_feature_test['input_ids']
  input_masks = data_feature_test['input_masks']
  input_segment_ids = data_feature_test['input_segment_ids']
  answer_labels = data_feature_test['answer_labels']
  test_dataset = make_dataset(input_ids = input_ids, input_masks = input_masks, input_segment_ids = input_segment_ids, answer_lables = answer_labels)

  train_dataloader = DataLoader(train_dataset,batch_size=16,shuffle=True)
  test_dataloader = DataLoader(test_dataset,batch_size=16,shuffle=True)
  running_loss_val = 0.0
  running_acc = 0.0
  for batch_index, batch_dict in enumerate(train_dataloader):
    model.train()
    batch_dict = tuple(t.to(device) for t in batch_dict)
    outputs = model(input_ids = batch_dict[0], labels = batch_dict[3])
    loss,logits = outputs[:2]
    loss.sum().backward()
    optimizer.step()
    # scheduler.step()  # Update learning rate schedule
    model.zero_grad()
          
    # compute the loss
    loss_t = loss.item()
    running_loss_val += (loss_t - running_loss_val) / (batch_index + 1)

    # compute the accuracy
    acc_t = compute_accuracy(logits, batch_dict[3])
    running_acc += (acc_t - running_acc) / (batch_index + 1)

    #log
    print("epoch:%2d batch:%4d train_loss:%2.4f train_acc:%3.4f"%(epoch+1, batch_index+1, running_loss_val, running_acc))
          
  running_loss_val = 0.0
  running_acc = 0.0
  for batch_index, batch_dict in enumerate(test_dataloader):
    model.eval()
    batch_dict = tuple(t.to(device) for t in batch_dict)
    outputs = model(input_ids = batch_dict[0], token_type_ids = batch_dict[1], attention_mask = batch_dict[2], labels = batch_dict[3])
    loss,logits = outputs[:2]
              
    # compute the loss
    loss_t = loss.item()
    running_loss_val += (loss_t - running_loss_val) / (batch_index + 1)

    # compute the accuracy
    acc_t = compute_accuracy(logits, batch_dict[3])
    running_acc += (acc_t - running_acc) / (batch_index + 1)

    # log
    print("epoch:%2d batch:%4d test_loss:%2.4f test_acc:%3.4f"%(epoch+1, batch_index+1, running_loss_val, running_acc))

model_to_save = model.module if hasattr(model, 'module') else model  # Take care of distributed/parallel training
print(model_to_save)
model_to_save.save_pretrained(r'/content/drive/My Drive/Colab Notebooks/model')
pkl_file = open(r'/content/drive/My Drive/Colab Notebooks/trained_model/data_features.pkl', 'rb')
data_features = pickle.load(pkl_file)

model_setting = {
         "config_file_path":r"/content/drive/My Drive/Colab Notebooks/model/config.json", 
         "model_file_path":r"/content/drive/My Drive/Colab Notebooks/model/pytorch_model.bin", 
         "vocab_file_path":r"albert/albert_tiny/vocab.txt",
         "num_labels":num_labels # 分幾類
     }
model, tokenizer = use_model(**model_setting)

answer_dic = data_features['answer_dic']

model.eval()

    #
q_inputs = ['口乾舌燥',
            '頭暈目眩', 
            '失眠問題',
            '發燒不退',
            '憂鬱煩躁',
            '腸胃不適',
            '呼吸困難',
            '關節疼痛',
            '身體腫瘤']
for q_input in q_inputs:
    bert_ids = to_bert_ids(tokenizer,q_input)
    assert len(bert_ids) <= 512
    input_ids = torch.LongTensor(bert_ids).unsqueeze(0)

        # predict
    outputs = model(input_ids)
    predicts = outputs[:2]
    predicts = predicts[0]
    max_val = torch.max(predicts)
    label = (predicts == max_val).nonzero().numpy()[0][1]
    ans_label = answer_dic.to_text(label)
    print(q_input)
    print(ans_label)