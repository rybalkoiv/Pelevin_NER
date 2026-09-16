import json
from collections import defaultdict
from spacy import displacy

class Puskin_Dataset:
    def __init__(self) -> None:
        self.data = None
        self.number_of_samples = -1
        self.ids = []

    def load_dataset(self, dataset_path):
        # load the dataset and return it as JSON 
        with open(dataset_path, 'r', encoding = 'utf-8') as f:
            data = json.load(f)

        self.data = data
        self.number_of_samples = len(data)
        self.ids = [str(i) for i in range(len(data))]
    
    def get_sample_by_id(self, id):
        text = self.data[id]['text']
        entities = self.data[id]['entities']
        tokens = self.data[id]['tokens']
        BIO_Tags = self.data[id]['BIO_Tags']
        return text, entities, tokens, BIO_Tags
    
    def get_entites_by_type(self, type):
        D = defaultdict(list)
        for id_ in self.ids:
            entities = self.data[id_]['entities']
            for ent in entities:
                if ent[-1] == type:
                    D[id_].append(ent)
        return D
    
    def display_tags(self, sentence, entities):
        colors = {'PER':'#00ffbb', 'DATE':'#ffbb00', 'LOC':'#ff00ff', 'WORK-OF-ART':'#cedf0e'}
        options = {'colors':colors}

        XX = []
        for ent in entities:
            XX.append({"start":ent[0], "end":ent[1], "label":ent[2]})

        ex = [{"text": sentence,
            "ents": XX,
            "title": None}]
        
        return displacy.render(ex, style="ent", manual=True, options=options)
