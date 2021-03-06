import torch.nn as nn

from model_visitor.Create_userId import Create_userId

# target: visitor
class GMF(nn.Module):
    def __init__(self,
                 num_factor,
                 num_dayofweek,
                 num_time,
                 num_sex,
                 num_age,
                 num_month,
                 num_day,
                 num_destination,
                 use_pretrain,
                 use_NeuMF,
                 pretrained_GMF):
        super(GMF, self).__init__()
        self.use_pretrain = use_pretrain
        self.use_NeuMF = use_NeuMF
        self.pretrained_GMF = pretrained_GMF

        # user info로 userId output 만들 객체 생성
        self.Create_userId = Create_userId(num_factor=num_factor,
                                           num_dayofweek=num_dayofweek,
                                           num_time=num_time,
                                           num_sex=num_sex,
                                           num_age=num_age,
                                           num_month=num_month,
                                           num_day=num_day,
                                           use_pretrain=use_pretrain,
                                           pretrained_GMF=pretrained_GMF,
                                           pretrained_MLP=None,
                                           GMF_model=True)
        # itemId Embedding
        self.item_embedding = nn.Embedding(num_embeddings=num_destination,
                                           embedding_dim=num_factor)

        # 최종 predictive_size는 parser로 받은 num_factor로 맞춘다.
        predictive_size = num_factor
        self.predict_layer = nn.Linear(predictive_size, 1)
        # activation function은 LeakyReLU
        self.relu = nn.LeakyReLU()

        # NeuMF(with pretraining)을 사용할 때, pretrained GMF에서 embedding의 weight 불러오기
        if use_pretrain:
            self.item_embedding.weight.data.copy_(
                self.pretrained_GMF.item_embedding.weight)
        # NeuMF(with pretraining)을 사용하지 않고 NeuMF용 GMF가 아닐때, predict_layer initialization
        else:
            if not use_NeuMF:
                # Layer weight initialization
                # nn.init.uniform_(self.predict_layer.weight)
                # nn.init.normal_(self.predict_layer.weight)
                # nn.init.xavier_uniform_(self.predict_layer.weight)
                nn.init.kaiming_uniform_(self.predict_layer.weight)

        # Embedding weight initialization(normal|uniform)
        nn.init.normal_(self.item_embedding.weight, mean=0.0, std=0.1)
        #nn.init.uniform_(self.item_embedding.weight, a=-1, b=1)


    def forward(self, dayofweek, time, sex, age, month, day, destination):
        destination_embedded = self.item_embedding(destination)
        # element wise product
        vector = self.Create_userId(dayofweek, time, sex, age, month, day) * destination_embedded
        # print('GMF ouput shape', output_GMF.shape)

        if self.use_NeuMF == False:
            output_GMF = self.predict_layer(vector)
            output_GMF = self.relu(output_GMF)
            output_GMF = output_GMF.view(-1)
        else:
            output_GMF = vector

        return output_GMF