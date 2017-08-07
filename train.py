import os
import sys
import torch
import torch.autograd as autograd
import torch.nn.functional as F


def train(train_loader, dev_loader, model, args):
    if args.cuda:
        model.cuda()

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    steps = 0
    model.train()
    for epoch in range(1, args.epochs+1):
        for i_batch, sample_batched in enumerate(train_loader):
            inputs = sample_batched['data']
            target = sample_batched['label']
            print('type(target): ', type(target))
            target.sub_(1)
            
            print('type(inputs): ', type(inputs))
            print('type(target): ', type(target))
        # for batch in train_iter:
            # inputs, target = batch.text, batch.label
            # print('\n')
            # print('inputs[:,0]', inputs[:,0])
            # print('target', target)


            # inputs.data.t_(), target.data.sub_(1)  # batch first, index align
            if args.cuda:
                inputs, target = inputs.cuda(), target.cuda()

            inputs = autograd.Variable(inputs)
            target = autograd.Variable(target)

            optimizer.zero_grad()
            logit = model(inputs)
            print(type(logit))
            print(type(target))

            #print('logit vector', logit.size())
            #print('target vector', target.size())

            # loss = F.nll_loss(logit, target)

            loss = F.cross_entropy(logit, target)
            loss.backward()
            optimizer.step()

            steps += 1
            if steps % args.log_interval == 0:
                corrects = (torch.max(logit, 1)[1].view(target.size()).data == target.data).sum()
                accuracy = 100.0 * corrects/args.batch_size
                sys.stdout.write(
                    '\rBatch[{}] - loss: {:.6f}  acc: {:.4f}%({}/{})'.format(steps, 
                                                                             loss.data[0], 
                                                                             accuracy,
                                                                             corrects,
                                                                             args.batch_size))
            if steps % args.test_interval == 0:
                eval(dev_loader, model, args)
            if steps % args.save_interval == 0:
                if not os.path.isdir(args.save_dir): os.makedirs(args.save_dir)
                save_prefix = os.path.join(args.save_dir, 'snapshot')
                save_path = '{}_steps{}.pt'.format(save_prefix, steps)
                torch.save(model, save_path)


def eval(data_loader, model, args):
    model.eval()
    corrects, avg_loss = 0, 0
    # for batch in data_loader:
    for i_batch, sample_batched in enumerate(data_loader):
        inputs = sample_batched['data']
        target = sample_batched['label']
        target.sub_(1)
        # inputs, target = batch.text, batch.label
        # inputs.data.t_(), target.data.sub_(1)  # batch first, index align
        if args.cuda:
            inputs, target = inputs.cuda(), target.cuda()

        logit = model(inputs)
        # loss = F.cross_entropy(logit, target, size_average=False)
        loss = F.nll_loss(logit, target, size_average=False)


        avg_loss += loss.data[0]
        corrects += (torch.max(logit, 1)
                     [1].view(target.size()).data == target.data).sum()

    size = len(data_loader)
    avg_loss = loss.data[0]/size
    accuracy = 100.0 * corrects/size
    model.train()
    print('\nEvaluation - loss: {:.6f}  acc: {:.4f}%({}/{}) \n'.format(avg_loss, 
                                                                       accuracy, 
                                                                       corrects, 
                                                                       size))


def predict(text, model, text_field, label_feild):
    assert isinstance(text, str)
    model.eval()
    text = text_field.tokenize(text)
    text = text_field.preprocess(text)
    text = [[text_field.vocab.stoi[x] for x in text]]
    x = text_field.tensor_type(text)
    x = autograd.Variable(x, volatile=True)
    print(x)
    output = model(x)
    _, predicted = torch.max(output, 1)
    return label_feild.vocab.itos[predicted.data[0][0]+1]
