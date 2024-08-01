	var EventosEnum = {
      CCE : {codigo: 110110, nome: "Carta de Correção Eletrônica"},
      CANC: { codigo: 110111, nome: "Cancelamento pelo emitente" },
	  CANC_SUBSTITUICAO: { codigo: 110112, nome: "Cancelamento por substituição" },
      EPEC: { codigo: 110140, nome: "EPEC-Emissão em Contingência" }, 
      CONF_DEST : {codigo: 210200, nome: "Confirmação da Operação pelo Destinatário"},
      CIENCIA_OP_DEST : {codigo: 210210, nome: "Ciência da Operação pelo Destinatário"},
      DESC_OP_DEST : {codigo: 210220, nome: "Desconhecimento da Operação pelo Destinatário"},
      OP_NREALIZADA : {codigo: 210240, nome: "Operação não Realizada"},
      REG_PAS : {codigo: 610500, nome: "Registro Passagem NF-e"},
	  REG_PAS_DFE : {codigo: 0, nome: "Registro Passagem"},
	  REG_PAS_AUTOMATICO : {codigo: 0, nome: "Registro Passagem Automatico"},
      REG_PAS_BRID : {codigo: 610550, nome: "Registro Passagem NF-e BRId"},
      CANC_REG_PAS : {codigo: 610501, nome: "Cancelamento Registro Passagem NF-e"},
      CTE_AUT : {codigo: 610600, nome: "CT-e Autorizado"},
      CANC_CTE_AUT : {codigo: 610601, nome: "CT-e Cancelado"},      
      PED_PRORROGACAO: { codigo: 0, nome: "Pedido de Prorrogação" },
      PED_CANC_PRORROGACAO: { codigo: 0, nome: "Cancelamento de Pedido de Prorrogação" },
      PED_FISCO_PRORROGACAO: { codigo: 0, nome: "Fisco Resposta Pedido de Prorrogação / Cancelamento Prorrogação" },
      MDFE_AUT: { codigo: 610610, nome: "MDF-e Autorizado" },
      MDFE_CANC : {codigo: 610611, nome: "MDF-e Cancelado"},      
      VIST_SUFRAMA : {codigo: 990900, nome: "Vistoria SUFRAMA"},
	  AVERB_EXPORT : {codigo: 790700, nome: "Averbação Exportação"},
      INT_SUFRAMA : {codigo: 990910, nome: "Internalização SUFRAMA"},
	  NFE_REFERENCIADA : {codigo: 410300, nome: "NFe Referenciada"},
	  ALERTA_FISCO : {codigo: 0, nome: "Alerta de Irregularidade"}
    }; 
	
    $(document).ready(function() {
        $('.toggle').click(function() {
	        $(this).toggleClass('opened').next('.toggable').toggle();
        }).next('.toggable').hide();
        $('td > fieldset').addClass('fieldset-internal');
        if (getQuerystring('print')) {
            $('.toggle').click();
            window.print();
        }
    });
  
    
    function mostraAba(num)
    {
        $('.nft').hide(); //OK
        $('#botoes_nft li').removeClass('nftselected'); //OK
        $('#aba_nft_' + num).show(); //OK
        $('#tab_' + num).addClass('nftselected');
    }

    var janela = null;
    function visualizaEvento(idConteudo, nomeEvento)
    {      
        if(janela){
            janela.focus();
        }
        if (document.getElementById(idConteudo)) 
        {
            janela = window.open('', 'winNFeCompleta', 'top=50,left=50,width=800,height=800,scrollbars=yes,status=yes');
            var HTML = '';
            HTML += '		<html>';
            HTML += '			<head>';
            HTML += '				<title>Evento</title>';
            HTML += '				<LINK rel=\"STYLESHEET\" href=\"https://nfe-extranet.sefazvirtual.rs.gov.br/apl/nfe/programas/Estilos/xslt.css\" type=\"text/css\">';
            HTML += '			</head>';
            HTML += '		<body class="GeralXslt" style="overflow-y: inherit;"> ';
            HTML += document.getElementById(idConteudo).innerHTML;
            HTML += '        </body>';
            HTML += '		</html>';
            
            janela.document.write(HTML);
            janela.document.close();
        }
        else 
        {
          alert(nomeEvento + ' não disponível.');
        }
    }
    function finaliza()
    {
    try 
    {
        janela.close();
    } catch(e) 
    { 
    }
    }     
      
/*  
    <!-- 
      INICIO BLOCO EXCLUSIVO RS - REMOVER AO DISTRIBUIR XSLT
    -->
*/ 
      
      var janelaCmtOtc = null;
      function visualizaCmt(chave)
      {
      if(janelaCmtOtc) { janelaCmtOtc.focus(); }
      if( jQuery('#CmtOtc_' + chave).length > 0 )
      {
      var vet = jQuery('#CmtOtc_' + chave).val().split(';');

      janelaCmtOtc = window.open('', 'winCmt', 'top=50,left=50,width=800,height=500,scrollbars=yes,status=yes');
      var HTML = '<html><head>';
      HTML += '<LINK rel=\"STYLESHEET\" href=\"https://nfe-extranet.sefazvirtual.rs.gov.br/apl/nfe/Programas/Estilos/nfe-vis.css?rand=' + Math.random() + '\" type=\"text/css\">';
      HTML += '<LINK rel=\"STYLESHEET\" href=\"https://nfe-extranet.sefazvirtual.rs.gov.br/apl/nfe/programas/Estilos/xslt.css?rand=' + Math.random() + '\" type=\"text/css\">';
      HTML += '<title>Verificação de Trânsito</title></head><body>';
      HTML += '<input type="button" value="Imprimir" style="border: 1px solid black; background-color: #cccccc; margin-right: 10px;" onclick="window.print()">';
      HTML += '<input type="button" value="Fechar" style="border: 1px solid black; background-color: #cccccc;" onclick="window.close()">';

      /* ****** */

      HTML += '<fieldset class="GeralXslt">';

      HTML += '<legend class="titulo-aba">Verificação de Trânsito</legend>';

      HTML += '<table class="box NoBorderBottom">';
      HTML += '<tr class="col-1"><td><label>Mensagem de Alerta</label></td></tr>';
      HTML += '<tr class="col-1"><td><span class="multiline">' + vet[12] + '</span></td></tr>';
      HTML += '</table>';

      HTML += '<table class="box NoBorderTopBottom">';
      HTML += '<tr class="col-1">';
      HTML += '<td width="400"><label>Posto Fiscal</label></td>';
      HTML += '<td width="150"><label>Sentido na Via</label></td>';
      HTML += '<td><label>Nro Registro Passagem</label></td>';
      HTML += '</tr>';
      HTML += '<tr class="col-1">';
      HTML += '<td><span class="multiline">' + vet[11] + '</span></td>';
      HTML += '<td><span>' + ((vet[24] == 'I') ? 'Indeterminado' : ((vet[24] == 'E') ? 'Entrada na UF' : 'Saída da UF')) + '</span></td>';
      HTML += '<td><span>' + vet[23] + '</span></td>';
      HTML += '</tr>';
      HTML += '</table>';


      HTML += '<table  class="box NoBorderTopBottom">';
      HTML += '<tr class="col-1"><td><label>UF</label></td>';
      if (vet[5] != '') {
          HTML += '<td><label>CNPJ Emitente</label></td>';
      } else {
          HTML += '<td><label>CPF Emitente</label></td>';
      }
      HTML += '<td><label>Série/Número</label></td>';
      HTML += '<td><label>Tipo Emissão</label></td>';
      HTML += '</tr>';
      HTML += '<tr class="col-1"><td><span>' + vet[0] + '</span></td>';
      if (vet[5] != '') {
          HTML += '<td><span>' + vet[5] + '</span></td>';
      } else {
          HTML += '<td><span>' + vet[6] + '</span></td>';
      }
      HTML += '<td><span>' + vet[1] + '/' + vet[2] + '</span></td>';
      switch (vet[3]) {
          case '1': HTML += '<td><span>1 - Normal</span></td>'; break;
          case '2': HTML += '<td><span>2 - Contingência FS</span></td>'; break;
          case '3': HTML += '<td><span>3 - Contingência SCAN</span></td>'; break;
          case '4': HTML += '<td><span>4 - Contingência DPEC</span></td>'; break;
          case '5': HTML += '<td><span>5 - Contingência FS-DA</span></td>'; break;
      }
      HTML += '</tr>';
      HTML += '</table>';


      HTML += '<table  class="box NoBorderTopBottom">';
      HTML += '<tr class="col-1"><td><label>UF</label></td>';
      if (vet[7] != '') {
          HTML += '<td><label>CNPJ Destinatário</label></td>';
      } else {
          HTML += '<td><label>CPF Destinatário</label></td>';
      }
      HTML += '<td><label>Tipo Operação</label></td>';
      HTML += '<td><label>Dt. Emissão</label></td>';
      HTML += '</tr>';
      HTML += '<tr class="col-1"><td><span>' + vet[9] + '</span></td>';
      if (vet[7] != '') {
          HTML += '<td><span>' + vet[7] + '</span></td>';
      } else {
          HTML += '<td><span>' + vet[8] + '</span></td>';
      }
      switch (vet[4]) {
          case '0': HTML += '<td><span>0 - Entrada</span></td>'; break;
          case '1': HTML += '<td><span>1 - Saída</span></td>'; break;
      }
      var dt = vet[22].split('-');
      HTML += '<td><span>' + dt[2] + '/' + dt[1] + '/' + dt[0] + '</span></td>';
      HTML += '</tr>';
      HTML += '</table>';

      HTML += '<table  class="box NoBorderTopBottom">';
      HTML += '<tr class="col-1"><td><label>Valor Total</label></td>';
      HTML += '<td><label>Protocolo NF-e</label></td>';
      HTML += '<td><label>Data-Hora Passagem</label></td>';
      HTML += '</tr>';

      HTML += '<tr class="col-1"><td><span>' + vet[10] + '</span></td>';

      HTML += '<td><span>' + jQuery('#nProt').val() + '</span></td>';

      var dt = vet[21].split('T')[0].split('-');
      HTML += '<td><span>' + dt[2] + '/' + dt[1] + '/' + dt[0] + ' ' + vet[21].split('T')[1] + '</span></td>';
      HTML += '</tr>';
      HTML += '</table>';

      HTML += '<table  class="box NoBorderTop">';
      HTML += '<tr class="col-1"><td><label>Modal</label></td>';
      if (vet[13] == '1') {
          HTML += '<td><label>Veículo</label></td>';
          HTML += '<td><label>Carreta</label></td>';
          HTML += '<td><label>Carreta 2</label></td>';
      } else {
          HTML += '<td><label>Identificação do Transporte</label></td>';
      }
      HTML += '</tr>';
      HTML += '<tr class="col-1">';
      switch (vet[13]) {
          case '1': HTML += '<td><span>Rodoviário</span></td>'; break;
          case '2': HTML += '<td><span>Aéreo</span></td>'; break;
          case '3': HTML += '<td><span>Aquaviário</span></td>'; break;
          case '4': HTML += '<td><span>Ferroviário</span></td>'; break;
          case '5': HTML += '<td><span>Dutoviário</span></td>'; break;
          case '9': HTML += '<td><span>Outros</span></td>'; break;
      }
      if (vet[13] == '1') {
          HTML += '<td><span>' + vet[14] + ' - ' + vet[15] + '</span></td>';
          HTML += '<td><span>' + vet[16] + ' - ' + vet[17] + '</span></td>';
          HTML += '<td><span>' + vet[18] + ' - ' + vet[19] + '</span></td>';
      } else {
          HTML += '<td><span>' + vet[20] + '</span></td>';
      }
      HTML += '</tr>';
      HTML += '</table>';

      HTML += '</fieldset>';

      /* ****** */

      HTML += '<br />';
      HTML += '</body></html>';
      
      janelaCmtOtc.document.write(HTML);
      janelaCmtOtc.document.close();
      }
      else {
      alert('Verificação de Trânsito não disponível')
      }
      }

/*      <!-- 
      FIM BLOCO EXCLUSIVO RS - REMOVER AO DISTRIBUIR XSLT
    -->
*/

function getQuerystring(key, default_) {
	if (default_ == null) default_ = "";
	key = key.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
	var regex = new RegExp("[\\?&]" + key + "=([^&#]*)");
	var qs = regex.exec(window.location.href);
	if (qs == null) return default_;
	else return qs[1];
}

