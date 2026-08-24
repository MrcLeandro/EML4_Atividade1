**ETL de um dataset de Pokemons**

Trabalho realizado pelos alunos:
- Márcio Leandro
- Mônica Mendes
- Rudi Modena

ETL realizado na AWS com a seguinte arquitetura:
<img width="902" height="576" alt="image" src="https://github.com/user-attachments/assets/62437352-cf41-4b37-b959-4e236bc7fbc2" />

O dataset contem links para uma API com diversos dados de um Pokemon e o objetivo é iterar sobre cada link e extrair os seguintes dados:
- ID
- Nome
- Tipo(s)
- Altura
- Peso
- Quantidade de movimentos que o pokemon pode aprender.

  Os dados acima foram estruturados em um arquivo JSON, enviados para uma fila e depois armazenados em um banco de dados.
  Conforme a arquitetura apresentada, o ETL foi realizado na seguinte ordem:
  
  1 - Bucket S3 "dataset"  para armazenar os dados brutos (arquivo urls.txt). Esse arquivo deve ser lido uma vez ao dia.
  
  2 - Lambda_1 (extrair_dados_pokemon_dataset) com código python para iterar sobre cada url, buscar os dados solicitados e inseri- los de forma estruturada em um arquivo JSON. Para este lambda foi necessário desenvolver uma camada (lambda_layer_1) que roda    um contêiner python com a biblioteca "requests" que não é nativa do serviço AWS Lambda. O gatilho configurado para este Lambda é qualquer alteração no objeto do Bucket dataset. Neste serviço foram criadas políticas para permissão de leitura e escrita através das funções GetObject e PutObject.
  
  3 - Bucket S3 "dados_selecionados" que armazena o arquivo JSON criado pelo serviço lambda do item 2.
  
  4 - Lambda_2 (Envia_dados_fila) para ler o arquivo JSON e enfileirá-lo em um serviço SQS. Neste serviço foram criadas políticas para permissão de leitura e escrita através das funções GetObject e PutObject. O gatilho deste serviço é qualquer alteração no arquivo JSON.
  
  5 - Lambda_3 (Escreve_Banco_Dados) para escrever os dados da fila SQS em um serviço RDS com banco de dados MariaDB. Para este serviço foram criadas variáveis de ambiente com os dados de acesso ao banco de dados. Neste serviço foi criada uma política para diversas permissões necessárias para conexão com o banco de dados e uma camada lambda com um contêiner que roda a biblioteca do conector python "pymsql" para acesso ao MariaDB. O gatilho configurado é o envio de novos dados pelo serviço SQS.
  
  6 - O software DBeaver foi instalado e utilizado como client DB para acesso à tabela criada com os dados estruturados. O arquivo "processed_sqs_data_202608232154.sql" foi exportado com os dados da tabela, porém, somente o nome dos pokemons foi armazenado por alguma falha não encontrada no código.

  7 - Cálculo do custo:
  O arquivo urls.txt tem apenas 46 KB e o JSON tem 177 KB. A estimativa de preço para um ano com as condições especificadas é:
  <img width="1109" height="606" alt="image" src="https://github.com/user-attachments/assets/baa63d57-672e-43b3-911e-764afb75d33f" />

