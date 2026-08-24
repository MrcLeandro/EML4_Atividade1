***ETL de um dataset de Pokemons
**Trabalho realizado pelos alunos:
- Márcio Leandro
- Mônica Mendes
- Rudi Modena

ETL realizado na AWS com a seguinte arquitetura
<img width="902" height="576" alt="image" src="https://github.com/user-attachments/assets/62437352-cf41-4b37-b959-4e236bc7fbc2" />

O dataset contem links para uma API com diversos dados de um Pokemon e o objetivo é iterar sobre cada link e extrair os seguintes dados:
- ID
- Nome
- Tipo(s)
- Altura
- Peso
- Quantidade de movimentos que o pokemon pode aprender.

  Os dados acima foram estruturados em um arquivo JSON, enviados para uma fila e depois armazenados em um banco de dados.
