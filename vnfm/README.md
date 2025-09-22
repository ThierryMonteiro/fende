# FENDE VNF Manager

Este projeto é uma implementação de um VNF Manager para o projeto FENDE (Ecossistema federado para oferta, distribuição e execução de funções virtualizadas de rede). Nossa solução é baseada no [Tacker](https://wiki.openstack.org/wiki/Tacker) para gerenciar o ciclo de vida básico das VNFs.

Através deste VNF Manager é possível criar, remover e atualizar uma VNF. Além disso, um módulo de monitoramento pode ser utilizado para monitorar as VNFs instanciadas e coletar métricas para posterior análise.

## Pré-requisitos

* [Tacker](https://wiki.openstack.org/wiki/Tacker) - NFV Orchestrator (NFVO) e VNF Manager (VNFM)
* [OpenStack](https://www.openstack.org/) - Virtualized Infrastructure Manager (VIM)

## Configuração

O arquivo de configuração ([tacker.conf](tacker.conf)) contém informações relacionadas a autenticação do usuário responsável por realizar as requisições ao VNF Manager. Um arquivo exemplo é disponibilizado em ([tacker.conf.example](tacker.conf.example)).

O arquivo de configuração deve ser renomeado para "*tacker.conf*".

## Executando ações no VNF Manager

O arquivo principal do VNF Manager ([manager.py](manager.py)) contém as funções responsáveis pelo ciclo de vida básico das VNFs.

Em primeiro lugar, inicialize as classes necessárias:

```python
manager = Manager()
```

Utilize então as seguintes funções para gerenciar o ciclo de vida das VNFs:

#### Criar VNF:

```python
manager.vnf_create(vnfd, name, function)
```

#### Remover VNF:

```python
manager.vnf_delete(vnf_id)
```

#### Atualizar VNF:

```python
manager.vnf_update(vnf_id, vnf_update_file)
```

### Atualizar função da VNF:

```python
manager.vnf_function_update(vnf_id, function)
```

### Criar SFC:

```python
manager.sfc_create(vnffgd, vnf_mapping)
```

### Remover SFC:

```python
manager.sfc_delete(vnffg_id, vnffgd_id)
```

### Parar função da VNF:

```python
manager.vnf_stop(vnf_id)
```

### Reiniciar função da VNF:

```python
manager.vnf_restart(vnf_id)
```

## Conteúdo do projeto

 * [manager.py](./manager.py) - Implementação do VNF Manager
 * [tacker.py](./tacker.py) - Implementação da API do Tacker
 * [element_management.py](./element_management.py) - Implementação do Element Management
 * [tacker.conf.example](./tacker.conf.example) - Arquivo exemplo de configuração
 * [utils.py](./utils.py) - Arquivo de funções auxiliares

## Licença

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
