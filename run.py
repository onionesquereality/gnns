import time
import numpy as np
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.nn.functional as F
import utils
from utils.load_gabor import load_dataset, load_graphs_targets_pickle, manual_split
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sklearn.metrics import mean_squared_error
from models.molecfingerprint import MolecFingerprintNet
from data.load import load_dataset
import argparse
import torch.optim as optim
import pdb

LOG = False

def eval_model(net, graphs, targets):
    outputs = net(graphs).data # a torch tensor
    targets = torch.Tensor(targets)
    diff = outputs - targets

    results = {}
    results['rmse'] = np.sqrt(torch.mean(diff.mul(diff)))
    results['mae'] = torch.mean(torch.abs(diff))
    return results

def logline(fname, line):
    line = time.strftime('[%H:%M:%S] ') + line
    print(line)
    if not LOG:
        return
    with open(fname, 'a') as f:
        if line[-1] != '\n':
            line = line + '\n'
        f.write(line)

def get_logger(dataset, lvls, hidden):
    logfname = '/stage/risigroup/NIPS-2017/Experiments-%s/reports/molec_lvl%d_hidden%d.txt' \
                %(dataset, lvls, hidden)
    log = lambda x: logline(logfname, x)
    return log

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="dataset", type=str, help="name of the dataset", default='qm9')
    parser.add_argument("-l", dest="levels", type=int, help="number of layers")
    parser.add_argument("-hi",dest="hidden", type=int, help="size of hidden layers")
    parser.add_argument("-b", dest="batchsize", type=int, help="batch size")
    parser.add_argument("-e", dest="epochs", type=int, help="max epochs")
    parser.add_argument("-lr",dest="learning_rate", type=float, help="initial learning rate")
    parser.add_argument("-o", dest="optimizer", type=str, help="optimizer")
    return parser.parse_args()

def make_model(nfeatures, hidden_size, levels):
    nfeatures = 5 #C, H, O, F, N
    model = MolecFingerprintNet(args.levels, nfeatures, hidden_size, F.relu)
    return model

def print_epoch_results(epoch, train_results, val_results):
    result =  "Epoch {} | train rmse: {:.3f} train mae: {:.3f}"
    result += "| val rmse: {:.3f} val mae: {:.3f}"
    result.format(epoch, train_results['rmse'], train_results['mae'],
                  val_results['rmse'], val_results['mae'])
    print result

def main():
    log = get_logger("Gabor", 4, 5)
    log('Epoch 10 | rmse 3.4')
    log('Epoch 10 | rmse 5.4')
    log('Epoch 10 | rmse 3.6')
    log('Epoch 10 | rmse 3.4')
    pdb.set_trace()
    args = get_args()
    data = load_dataset(args.dataset)

    model = make_model(nfeatures, args.hidden, args.levels)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.MSELoss()
    for epoch in range(args.epochs):
        for i in range(0, len(data['g_train']), batchsize):
            g_batch = data['g_train'][i:i+batchsize]
            y_batch = Variable(torch.Tensor(data['y_train'][i:i+batchsize]))

            optimizer.zero_grad()
            outputs = model.forward(g_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()

        train_res = eval_model(model, data['g_train'], data['y_train'])
        val_res = eval_model(model, data['g_val'], data['y_val'])
        print_epoch_results(epoch, train_res, val_res)

        # Stop training if the validation error stops decreasing
        if val_res['rmse'] > prev_val_rmse and epoch > 4: # do at least 5 epochs
            break

        data['g_train'], data['y_train'] = shuffle(data['g_train'], data['y_train'])

if __name__ == '__main__':
    main()