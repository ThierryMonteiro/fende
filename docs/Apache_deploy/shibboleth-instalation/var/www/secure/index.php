<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <!-- Aplicação Homologa para validar os atributos liberados pelo IdP do usuário que validou o login. -->
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>CAFe Expresso - Homologação de Atributos</title>

    <meta name="description" content="Provedor de Serviço da CAFe Expresso Comunidade Acadêmica Federada para Experimentação">

        <!-- Normalize -->
        <link rel="stylesheet" type="text/css" href="//cdnjs.cloudflare.com/ajax/libs/normalize/3.0.2/normalize.min.css" />
        <!-- Bootstrap -->
        <link rel="stylesheet" type="text/css" href="//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.4/css/bootstrap.min.css" />
        <!-- Local Style -->
                <link rel="stylesheet" type="text/css" href="/css/estilo.css">
                <!-- Favicon -->
                <link rel="icon" href="/img/favicon.png">

        <!-- jQuery -->
        <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
        <!-- Modernizr -->
        <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/modernizr/2.8.3/modernizr.min.js"></script>
        <!-- Bootstrap -->
        <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.4/js/bootstrap.min.js"></script>

    <!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
                <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/html5shiv/3.7.2/html5shiv.min.js"></script>
                <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/respond.js/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>

    <nav class="navbar navbar-default navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Menu</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="/">Serviço de Homologação de Atributos</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
                  <ul class="nav navbar-nav navbar-right">
                    <li>
                          <a href="#" id="openSobreCafe" data-toggle="modal" data-target="#sobreCafe">Sobre</a>
                        </li>
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">Contato <span class="caret"></span></a>
              <ul class="dropdown-menu" role="menu">
                            <li class="dropdown-header">Contato</li>
                <li><a href="mailto:gidlab@rnp.br">gidlab@rnp.br</a></li>
                <li class="divider"></li>
                <li class="dropdown-header">Suporte</li>
                <li><a href="mailto:experimentosgidlab@rt.rnp.br">experimentosgidlab@rt.rnp.br</a></li>
              </ul>
            </li>
                  </ul>
        </div>
      </div>
    </nav>

    <div class="container main">
                <div class="page-header">
                        <h3>Serviço de Homologação de Atributos</h3>
                </div>

                <section>
            <div class="panel panel-default">
              <div class="panel-heading"><strong>Atributos Usuário</strong></div>
                          <div class="panel-body">
                                  <table class="table table-striped table-atributos">
                                        <thead>
                                          <tr>
                                                <th>Atributo</th>
                                                <th>Valor</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                        <?php
                                          foreach($_SERVER as $atributo => $valor) {
                                                if(
                                                  strpos($atributo, 'Shib') === 0
                                                  &&
                                                  strpos($atributo, 'Person') !== false
                                                ) {
                                                                                                          echo "<tr>";
                                                                                                          echo "<td>{$atributo}</td><td>{$valor}</td>";
                                                                                                          echo "</tr>";
                                                }
                                          }
                                        ?>
                                        </tbody>
                                  </table>
                          </div>
            </div>

            <div class="panel panel-default">
              <div class="panel-heading"><strong>Atributos Shibboleth</strong></div>
                          <table class="table table-striped">
                                <thead>
                                  <tr>
                                        <th>Atributo</th>
                                        <th>Valor</th>
                                  </tr>
                                </thead>
                                <tbody>
                                <?php
                                  foreach($_SERVER as $atributo => $valor) {
                                        if(
                                          strpos($atributo, 'Shib') === 0
                                          &&
                                          strpos($atributo, 'Person') === false
                                        ) {
                                          echo "<tr>";
                                          echo "<td>{$atributo}</td><td>{$valor}</td>";
                                          echo "</tr>";
                                        }
                                  }
                                ?>
                                </tbody>
                          </table>
            </div>
                </section>
    </div> <!-- main -->

    <footer class="footer">
      <div class="container">
                <div class="row">
                        <div class="col-xs-12 col-sm-4">
                                <p class="text-left"><img src="/img/cafe.png" alt="CAFe Expresso"/></p>
                        </div>
                        <div class="col-xs-12 col-sm-8">
                                <p class="text-right"><img src="/img/rodape.png" alt="RNP"/></p>
                        </div>
                </div>
      </div>
    </footer>

        <!-- Modal Sobre -->
        <div class="modal fade" id="sobreCafe" tabindex="-1" role="dialog" aria-labelledby="sobreCafe" aria-hidden="true">
          <div class="modal-dialog">
                <div class="modal-content">
                  <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal" aria-label="Fechar"><span aria-hidden="true">&times;</span></button>
                        <h4 class="modal-title" id="sobreCafeTitle">Sobre a CAFe Expresso</h4>
                  </div>
                  <div class="modal-body" id="sobreCafeContent">
					  <p>
						CAFe Expresso consiste em um ambiente para experimentação das principais tecnologias
						para gerenciamento de identidade, oferecendo provedores de identida de e de serviços
						Shibboleth, visando facilitar experimentos de pesquisadores que queiram desenvolver
						soluções para federações Shibboleth, como é o caso da Federação CAFe da RNP.
					  </p>
					  <p>
						A CAFe Expresso, oferece três provedores de identidade (IdPs), três prov edores de serviço
						(SPs) configurados para hospedar aplicações PHP, Java e Python, e dois diferentes serviços
						de descoberta, Discovery Service (DS), um chamado WAYF e outro chamado Embbeded DS.
						Também oferece o serviço uApprove, que permite ao usuário saber previamente quais atributos
						(informações) estão sendo solicitados pelo SP que deseja acessar.
					  </p>
					  <p>
						O pesquisador tem ainda a liberdade de baixar imagens de máquinas virtuais com provedor
						de identidade, provedor de serviço e WAYF/DS (Where Are You From/Discovery Service) Shibboleth,
						prontos para uso. Dessa forma, o pesquisador poderá montar uma federação Shibboleth em sua
						própria instituição. Contudo, caso o pesquisador não tenha recursos, computacionais ou mesmo de pessoas,
						para gerir sua própria federação, o CAFe Expresso está a disposição 24 horas para seu uso.
					  </p>
                  </div>
                  <div class="modal-footer">
                        <button type="button" class="btn btn-default" data-dismiss="modal">Fechar</button>
                  </div>
                </div>
          </div>
        </div>
  </body>
</html>

