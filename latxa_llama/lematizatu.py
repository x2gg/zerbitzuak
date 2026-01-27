import os
import numpy as np
import pandas as pd
from datasets import load_dataset
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

# Model and tokenizer setup
model_name_or_path = "HiTZ/xlm-roberta-large-lemma-eu"
task_name = "ner"
model_revision = "main"
output_dir = "./output"


# Load model configuration
config = AutoConfig.from_pretrained(
    model_name_or_path,
    finetuning_task=task_name,
    cache_dir=None,
    revision=model_revision,
    use_auth_token=None,
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_name_or_path,
    cache_dir=None,
    use_fast=True,
    revision=model_revision,
    use_auth_token=None,
    add_prefix_space=True
)

# Load model
model = AutoModelForTokenClassification.from_pretrained(
    model_name_or_path,
    from_tf=False,
    config=config,
    cache_dir=None,
    revision=model_revision,
    use_auth_token=None,
)


def lemmatize_text(test_file):

    # Load the test dataset from TSV
    dataset = load_dataset('csv', data_files={'test': test_file}, delimiter='\t')

    # Preprocess dataset: Tokenization
    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples['text'],
            truncation=True,
            max_length=32,
        )
        return tokenized_inputs

    # Apply the tokenization function to the dataset
    test_dataset = dataset["test"].map(tokenize_and_align_labels, batched=True)

    # Remove any columns that aren't needed (like 'text')
    test_dataset = test_dataset.remove_columns(['text'])

    # Setup training arguments (even for prediction we need these)
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_eval_batch_size=256,  
        do_predict=True,
        overwrite_output_dir=True,
        fp16=True,
        
    )

    # Data collator (for dynamic padding)
    data_collator = DataCollatorForTokenClassification(tokenizer)

    # Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        data_collator=data_collator
    )

    # Make predictions
    predictions, _, _ = trainer.predict(test_dataset)

    # Decode predictions: Get the highest scoring class (argmax) for each token
    predictions = np.argmax(predictions, axis=2)
    #print(predictions)
    #print(np.unravel_index(np.argmax(predictions, axis=None), predictions.shape))
    puntuazio_max = []
    for p in predictions: 
        ind = np.unravel_index(np.argmax(p, axis=None), p.shape)
        indize_max = ind[0].item()
        puntuazio_max.append(indize_max)

    #print(puntuazio_max)


    id2label = model.config.id2label
    true_predictions = []
    for prediction in predictions:
        pred_labels = [id2label.get(p, "UNK") for p in prediction]
        true_predictions.append(pred_labels)

    #print(true_predictions)
    true_predictions_2 = []
    for pMax_ind, truePred in zip(puntuazio_max, true_predictions):
        true_predictions_2.append(truePred[pMax_ind])

    #print(true_predictions_2)
    # Save predictions in the desired lemma format
    base_name = os.path.splitext(os.path.basename(test_file))[0]
    df = pd.read_csv(test_file, delimiter='\t')  # Read the TSV file into a DataFrame
    original_words = df['text'].tolist()
    # Create the output name
    name = f"{base_name}_lematizatuta.tsv"  
    output_test_predictions_file = os.path.join(training_args.output_dir, name )
    if trainer.is_world_process_zero():
        with open(output_test_predictions_file, "w", encoding='utf-8') as writer:
            for prediction, og_word in zip(true_predictions_2,original_words):
                # Join the lemmas and write to file
                writer.write(f"{og_word} {prediction}\n")
    

