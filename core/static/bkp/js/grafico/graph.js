$(document).ready(function() {
    $(window).on("load", function (e) {
        
        /*
        * Variaveis utilizadas para gerenciar gráficos criados ou que serão criados
        * utilizada para excluir ou reconstruir um gráfico a partir do select
        */
        var graphs = [];
        var times = [];
        var VNFs = [];
        var url = [];
        var interval = [];
        var VNFName = [];

        /*Inicialização dos gráficos*/
        setTimeout(__iniGraph, 1500);

        /* Dicionario de VNFs */
        $("#selectedVNFs option").each(function(){
            if($(this).text() != 'Global'){
                VNFName[$(this).val()] = $(this).text();
            }
        });
       
        /* Inicialização de gráficos, predeterminação dos dados para gerar os gráficos*/
        function __iniGraph() {
            VNFs = [];
            getTimesSelected();
            /* Inicializa os checkbox */
            list = ['CPU', 'Memory', 'Disk', 'Network'];
            list.map(function (item) {
                getGraphSelected(item, true);
            });
            /* Inicializa os checkbox */
            getVNFsSelected();
            montaURL(times['time_range']['seconds']);
            createGraph();
        }     

      
        /*
        * Retorna URL montada para executar o ajax
        */
        function montaURL(time = 15) {
            var dicionario = {
                CPU: "cpu_usage",
                Memory: "memory_usage",
                Disk: "disk_usage",
            };
            limit = times.time_range.seconds / 5;
            url = [];
            /*UFSM*/
            var base = "http://200.18.45.126:8086/query?pretty=true&u=leitor&p=leitor_gtfende&db=vnfs&q=SELECT%20";
            /*UFRGS */
            //var base = "http://gt-fende.inf.ufrgs.br:8086/query?pretty=true&u=coletor&p=gtfende&db=vnfs&q=SELECT%20";
            for (let i = 0; i < VNFs[0].length; i++) {
                var URI = [];
                jQuery.map(Object.keys(graphs), function (key, index) {
                    if (key == 'Network') {
                        var UPDOWN = {
                            Net_rx: [
                            (base + "%22net_rx%22%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22%20WHERE%20time%20%3E%20now()%20-%20" + time + "s"),
                            (base + "last(net_rx)%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22"),
                            (base + "%22net_rx%22%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22%20ORDER%20BY%20%22time%22%20DESC%20LIMIT%20" + limit),
                            ],
                            Net_tx: [
                            (base + "%22net_tx%22%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22%20WHERE%20time%20%3E%20now()%20-%20" + time + "s"),
                            (base + "last(net_tx)%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22"),
                            (base + "%22net_tx%22%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22%20ORDER%20BY%20%22time%22%20DESC%20LIMIT%20" + limit),
                            ]
                        };
                        URI[key] = UPDOWN;
                    } else {
                        URI[key] = [
                        (base + '%22' + dicionario[key] + "%22%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22%20WHERE%20time%20%3E%20now()%20-%20" + time + "s"),
                        (base + 'last(' + dicionario[key] + ")%20FROM%20%22vnfs%22.%22autogen%22.%22" + VNFs[0][i] + "%22"),
                        (base + '%22' + dicionario[key] + '%22%20FROM%20%22vnfs%22.%22autogen%22.%22' + VNFs[0][i] + '%22%20ORDER%20BY%20%22time%22%20DESC%20LIMIT%20' + limit),
                        ];
                    }
                });
                url.push(URI);
            }
        }

        /*
        * Retorna quais gráficos estão selecionados para serem exibidos
        */

        function getGraphSelected(checkbox, init = false) {
            if ($(".checkbox-" + checkbox + "[type='checkbox']").is(":checked")) {
                graphs[checkbox] = 0;
                if (init == false) {
                    montaURL(times['time_range']['seconds']);
                    createGraph();
                }
            } else {
                clearInterval(interval[checkbox]);
                delete_graphs(checkbox);
                delete interval[checkbox];
                delete url[checkbox];
                delete graphs[checkbox];
            }
        }

        /*
        * Retorna valores referentes ao tempo, tempo de atualização e a lacuna de tempo do gráfico
        */
        function getTimesSelected() {
            //Variaveis
            var time_range = [];
            var update_time = [];
            var minutes = 'minutes';
            var seconds = 'seconds';
            var milliseconds = 'milliseconds';
            
            /* Time Range */
            var el = parseInt($("#time_range :selected").val());
            time_range[minutes] = el;
            time_range[seconds] = el * 60;
            
            /* Update Time */
            var el = parseInt($("#update_time :selected").val());
            update_time[seconds] = el;
            update_time[milliseconds] = el * 1000;
            
            /*Atualização da variavel global*/
            times['time_range'] = time_range;
            times['update_time'] = update_time;
        }

            /*
            * Retorna valores referentes a quais ou qual VNFs deve ser exibido
            */
            function getVNFsSelected() {
                var str = $("#selectedVNFs :selected").val();
                VNFs.push(str.split(","));
            }


        function createGraph() {
            /* TODO COLORS */
            mode = 'lines+markers';
            color = null;
            group = null;
            graphError = null;
            jQuery.map(Object.keys(url[0]), function (key) {
                var data = [];
                if (key == 'Network') {
                    /*
                    * Verificação se já foi criado o gráfico, se já foi apenas o intervalo pode ser acessado
                    * Caso não, ambos serão acessados
                    */
                    if( graphs[key] == 0 ) {
                        /*
                        * Utiliza o net_rx da primaira vnf e o net_tx da última, caso seja apenas 1 irá utilizar do mesmo
                        */
                        data.push(getInfluxValue(url[0].Network.Net_rx[2], mode, color, 'Upload'));
                        data.push(getInfluxValue(url[VNFs[0].length - 1].Network.Net_tx[2], mode, color, 'Download'));
                        
                        if (data[0] != "Dados para criação do gráfico não encontrado") {
                            /*
                            * Monta o gráfico na tela, necessita de um elemento com id igual ao nome enviado na key
                            */
                            $('#'+key).empty();
                            graphs[key] = Plotly.plot(key, data, createLayout(key, 'Average Bandwidth (Bps)'));
                        } else {
                            /*
                            * Adiciona mensagem caso não seja encontrado dados
                            */
                            $('#'+key).empty().append('<div class="alert alert-danger" role="alert"><h4 class="alert-heading">!'+key+'</h4><p class="mb-0">'+data[0]+'</p></div>');
                            graphError = true;
                        }
                    }
                    /* Cria o loop para atualização do gráfico periodicamente */
                    interval[key] = setInterval(function () {
                        var dados_net_rx = getInfluxValue(url[0].Network.Net_rx[1], mode, color, 'Upload', null, null, true);
                        var dados_net_tx = getInfluxValue(url[VNFs[0].length - 1].Network.Net_tx[1], mode, color, 'Download', null, null, true);
                        /* 
                        * Parar atualização caso influx pare de funcionar
                        */
                        if( dados_net_rx == "Dados para criação do gráfico não encontrado" || dados_net_tx == "Dados para criação do gráfico não encontrado" ){
                            clearInterval(interval[key]);
                            return;
                        } else {
                            var chartData = {
                                'x': [
                                [dados_net_rx['valoresX'][0]],
                                [dados_net_tx['valoresX'][0]],
                                ],
                                'y': [
                                [dados_net_rx['valoresY'][0]],
                                [dados_net_tx['valoresY'][0]],
                                ],
                            };
                            updateChart(chartData, key, times.time_range.minutes);
                        }
                    }, times.update_time.milliseconds);
                } else {
                    /*
                    * Verificação se já foi criado o gráfico, se já foi apenas o intervalo pode ser acessado
                    * Caso não, ambos serão acessados
                    */
                    if( graphs[key] == 0 ) {
                        for (let index = 0; index < url.length; index++) {
                            /*
                            * Recebe o nome do VNFs para layout lateral do gráfico
                            */
                            for(chave in VNFName){
                                if( url[index][key][2].search(chave) != -1){
                                    name = VNFName[chave];
                                }
                            }
                            data.push(getInfluxValue(url[index][key][2], mode, color, name));
                        }
                        if ( data[0] != "Dados para criação do gráfico não encontrado" ) {
                            /*
                            * Monta o gráfico na tela, necessita de um elemento com id igual ao nome enviado na key
                            */
                           $('#'+key).empty();
                            graphs[key] = Plotly.plot(key, data, createLayout(key));
                        } else {
                            /*
                            * Adiciona mensagem caso não seja encontrado dados
                            */
                            $('#'+key).empty().append('<div class="alert alert-danger" role="alert"><h4 class="alert-heading">!'+key+'</h4><p class="mb-0">'+data[0]+'</p></div>');
                            graphError = true;
                        }
                    }
                    /* Cria o loop para atualização do gráfico periodicamente */
                    interval[key] = setInterval(function () {
                        var x = [];
                        var y = [];
                        var error = 0;
                        for (let index = 0; index < url.length; index++) {
                            dadosInflux = getInfluxValue(url[index][key][1], null, null, null, null, null, true);
                            if(dadosInflux != "Dados para criação do gráfico não encontrado"){
                                x.push([dadosInflux['valoresX'][0]]);
                                y.push([dadosInflux['valoresY'][0]]);
                            } else {
                                error++;
                            }
                        }
                        /* 
                        * Parar atualização caso influx pare de funcionar
                        */
                        if( error == url.length ){
                            clearInterval(interval[key]);
                            return;
                        } else {
                            var chartData = {
                                'x': x,
                                'y': y,
                            };
                            updateChart(chartData, key, times.time_range.minutes);
                        }
                    }, times.update_time.milliseconds);
                }
            });
            /* Nova tentativa de conseguir os dados*/
            if(graphError == true){
                setTimeout(createGraph, 15000);
            }
        }

        /*
        * Função para destruir gráficos selectionado ou todos se desejar
        */
        function delete_graphs(name = null, all = false) {
            if (all == true) {
                list = ['CPU', 'Memory', 'Disk', 'Network'];
                list.map(function (item) {
                    delete_graphs(item);
                });
            }
            if (name) {
                Plotly.purge(name);
                $('#'+name).empty();
            }
        }

        /*
        * Cria o layout do gráfico
        */
        function createLayout(chartName, title = 'Percent (%)') {
            var layout = {
                title: chartName,
                yaxis: {
                    title: title,
                },
                
                margin: {
                    l: 50,
                    r: 50,
                    t: 50,
                    b: 50,
                },
                height: '250',
                showlegend: true
            };
            return layout;
        }

        /*Retorna os valores gerados pela url informada, padrão recebido pelo influxdb*/
        function getInfluxValue(url, mode = null, color = null, name = null, fill = null, group = null, last = false) {
            var retorno;
            $.ajax({
                url: url,
                type: 'GET',
                async: false,
                contentType: 'application/json',
                timeout: 2000,
                data: {
                    retorno: retorno,
                },
                success: (data) => {
                    if ("series" in data.results[0]) {
                        var values = data.results[0].series[0].values;
                        var valoresX = [];
                        var valoresY = [];
                        for (var i = 0; i < values.length; i++) {
                            valoresX.push(new Date(values[i][0]));
                            valoresY.push(values[i][1]);
                        }
                        if (last == false) {
                            retorno = {
                                x: valoresX.reverse(),
                                y: valoresY.reverse(),
                                stackgroup: group,
                                mode: mode,
                                fill: fill,
                                line: { 
                                    color: color,
                                },
                                connectgaps: true,
                                name: name,
                            };
                        } else {
                            retorno = {
                                valoresX,
                                valoresY,
                            };
                        }
                    } else {
                        /* Mensagem exibida caso não seja encontrado dados no influx */
                        retorno = 'Dados para criação do gráfico não encontrado';
                    }
                }
            });
            return (retorno);
        };


        /*
        * Função para atualização periodica do gráfico
        */
        function updateChart(chartData, name, time_range = 1) {
            var cnt = 0;
            var time = new Date();
            /* Gera variavel com o size do array */
            var count = chartData.x.length;
            var extendNumbers = [];
            for (var i = 0; i < count; i++)
                extendNumbers.push(i);
            var update = {
                x: chartData.x,
                y: chartData.y
            }
            var olderTime = chartData.x[0][0].setMinutes(chartData.x[0][0].getMinutes() - parseInt(time_range));
            var futureTime = chartData.x[0][0].setMinutes(chartData.x[0][0].getMinutes() + parseInt(time_range));
            var minuteView = {
                xaxis: {
                    type: 'date',
                    range: [olderTime, futureTime]
                },
            };
            Plotly.relayout(name, minuteView);
            Plotly.extendTraces(name, update, extendNumbers)
        };


        /*
        * Atualização dos checkbox
        */
        $(".radio-graph [type='checkbox']").on('change', function () {
            var checkbox = $(this).attr("name");
            getGraphSelected(checkbox);
        });

        /*
        * Atualização do Service
        */
        $("#selectedVNFs").on('change', function () {
            delete_graphs(null, true);
            __iniGraph();
        });

        /*
        * Atualização do time_range
        */
        $("#time_range").change(function () {
            delete_graphs(null, true);
            __iniGraph();
        });

        /*
        * Atualização do time_range
        */
        $("#update_time").change(function () {
            /* Atualiza dados da variavel */
            getTimesSelected();
            // Limpa todos as funções interval
            list = ['CPU', 'Memory', 'Disk', 'Network'];
            list.map(function (item) {
                /* Para a função setInterval */
                clearInterval(interval[item]);
                /* Deleta o id criado quando o Inverval é setado*/
                delete interval[item];
            });
            // Chama novamente a função de inicialização/update dos dados apartir do influx com o novo dado
            createGraph();
        });
    });
});