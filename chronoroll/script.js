<script src="https://unpkg.com/dsteem@^0.8.0/dist/dsteem.js"></script>


    var rpcnodes=[
        "https://api.steemit.com",
        "https://rpc.buildteam.io",
    ]
    var noderpc= rpcnodes ? rpcnodes[0] : (rpcnodes ? rpcnodes[1] : 'https://api.steemit.com')
    var client = new dsteem.Client(noderpc)
    sesion()
    var coin='STEEM'
    var to="chronoroll"
    var type="day"
    var steemc=false
    var hg=false
    function invesdata(){
        hg=true
        if(hg==true){
            document.getElementById("steemconnectV").disabled=true
        }
        client.database.getAccounts([user]).then(function (result) {
            var json=JSON.parse(result[0].json_metadata)
            if(json.profile.profile_image===undefined){
                document.getElementById("imgperfil").src="https://steemitimages.com/512x512/https://steemitimages.com/DQmb2HNSGKN3pakguJ4ChCRjgkVuDN9WniFRPmrxoJ4sjR4"
            }
            else{
                document.getElementById("imgperfil").src=json.profile.profile_image;
            }
            document.getElementById("perfil").innerHTML=result[0].name
            document.getElementById("steemcan").innerHTML=result[0].balance;
            document.getElementById("sbdcan").innerHTML=result[0].sbd_balance
                            
            setInterval(function(){
                client.database.getAccounts([user]).then(function (resty) {
                    var sasteem=parseFloat(document.getElementById("steemcan").value)
                    var sasbd=parseFloat(document.getElementById("sbdcan").value)
                    if(parseFloat(resty[0].balance)!=sasteem || parseFloat(resty[0].sbd_balance)!=sasbd){
                        document.getElementById("steemcan").innerHTML=resty[0].balance
                        document.getElementById("sbdcan").innerHTML=resty[0].sbd_balance
                    }
                })
            }, 1000);
        })
        var ty=document.getElementById("perfilpr")
        var sal=document.getElementById("saldos")
        sal.className ="card text-center"
        ty.className ="card text-center"

        tabladato()

    }
    function infouser(){
        var userstencot=document.getElementById("buqueuser").value
        if(userstencot){
                user=userstencot
                var du=document.getElementById("busqueuser")
                du.className="d-none"
                invesdata()
        }
    }
    function sesion(){
            document.getElementById("rolval").disabled=true;
            if(steemc==true){
                var ct=document.getElementById("busqueuser")
                ct.className=""
                document.getElementById("rolval").disabled=false;
                document.getElementById("ant").innerHTML="<p id='odometer'>click roll</p>"
            }
        
    }
    function numero(){
        var idoto=document.getElementById("typ").value
        odometer.innerHTML=idoto
        idoto=idoto.toLowerCase()
        var amountsend=document.getElementById("amountsteem").value
        amountsend=Math.floor(amountsend * 1000) / 1000;
        var cani=amountsend.toFixed(3)+" "+coin
        var canis=amountsend.toFixed(3)
        var porcen=parseFloat(document.getElementById("porcenta").value)
        var data1='{'+'"type":'+'"'+idoto+'"'+','+'"possibility"'+':'+porcen+'}'
        var memo=data1.toString()
        if(steemc==true){
            var altura=500;
            var anchura=560;
            var y=parseInt((window.screen.height/3)-(altura/3));
            var x=parseInt((window.screen.width/2)-(anchura/2));
            var dato="https://v2.steemconnect.com/sign/transfer?from=&to="+to+"&amount="+canis+"%20"+coin+"&memo="+data1
            window.open(dato, "steemconnect","width="+altura+",height="+anchura+",top="+y+",left="+x)
        }
        
    }
    function cambiomoneda(){
        if(coin=="STEEM"){
            coin="SBD"
            document.getElementById("coinmoney").innerHTML="SBD"
            cammbion()
        }else{
            coin="STEEM"
            document.getElementById("coinmoney").innerHTML="STEEM"
            cammbion()
        }
    }
    function cammbion(){
        var cantidad=document.getElementById("amountsteem").value
        var porcentactuldinput=(document.getElementById("porcenta").value)/100
        if(cantidad<0.1){
            document.getElementById("amountsteem").value=0.1
            var amount=(0.098*1*cantidad)/(0.1*porcentactuldinput)
            var al=amount.indexOf(".")
            var menssage="If you have the winning number, you will receive "+amount.toFixed(3)+" "+coin
            document.getElementById("ms").innerHTML=menssage
        }
        else if(cantidad>5){
            document.getElementById("amountsteem").value=5
            var amount=(0.098*1*cantidad)/(0.1*porcentactuldinput)
            var menssage="If you have the winning number, you will receive "+amount.toFixed(3)+" "+coin
            document.getElementById("ms").innerHTML=menssage
        }
        else {
            var amount=(0.098*1*cantidad)/(0.1*porcentactuldinput)
            var menssage="If you have the winning number, you will receive "+amount.toFixed(3)+" "+coin
            document.getElementById("ms").innerHTML=menssage
        }
    }
    function x2(){
        var dato=document.getElementById("amountsteem").value
        var multiple=parseFloat(dato)*2
        document.getElementById("amountsteem").value=multiple
        porcent()
    }
    function porcent(){
        var por=document.getElementById("porcenta").value
        var saldop=document.getElementById("amountsteem").value
        var tyd=(saldop*0.98*0.1)/0.025
        if(por<tyd){
            document.getElementById("porcenta").value=tyd
            cammbion()
        }
        if(por>99.99){
            document.getElementById("porcenta").value=99.99
            cammbion()
        }
        else {
            cammbion()
        }
    }
    function sortJSON(data, key, orden) {
    return data.sort(function (a, b) {
        var x = a[key],
        y = b[key];
        if (orden === 'asc') {
            return ((x < y) ? -1 : ((x > y) ? 1 : 0));
        }
        if (orden === 'desc') {
            return ((x > y) ? -1 : ((x < y) ? 1 : 0));
        }
    });
}
    function IsJsonString(str) { 
        try { JSON.parse(str); }
        catch (e) { return false; } 
        return true; 
    } 
    function tabladato(){
        var blocktest=[]
        setInterval(function testtabla(){
            client.database.call('get_account_history', [user, -1, 1000]).then(function (result) {
            var transfers = result.filter( tx => tx[1].op[0] =='transfer' && tx[1].op[1].to==to ||  tx[1].op[1].from==to)
            var asc=sortJSON(transfers,"[1].block","asc")
            asc.map(function(ele){
                
                if(ele[1].op[1].from==to){
                    var memofrom=ele[1].op[1].memo
                    var positionm=memofrom.indexOf(";")
                    var men=memofrom.substring(0,positionm)
                    //{}
                    if(blocktest.includes(ele[1].block)==false){
                        if(IsJsonString(men)==true){
                            blocktest.push((ele[1].block))
                            var json2=JSON.parse(men)
                            var datot=document.getElementById(json2.block).innerHTML
                            document.getElementById(json2.block).innerHTML=datot+"<td>"+json2.result+"</td>"
                        }
                    }
                }
                else if(ele[1].op[1].to==to){
                    ele[1].op[1].amount//cantidad enviada
                    var dating=ele[1].op[1].memo
                    if(blocktest.includes(ele[1].block)==false){
                        if(IsJsonString(dating)==true){
                            blocktest.push((ele[1].block))
                            var json1=JSON.parse(dating)
                            var resuldatotopush="<tr id="+ele[1].block+">"+"<td>"+ele[1].block+"</td>"+"<td>"+json1.type+"</td>"+"<td>"+json1.possibility+"</td>"+"</tr>"
                            var daytabla=document.getElementById("props").innerHTML
                            document.getElementById("props").innerHTML=daytabla+resuldatotopush
                        }
                    }
                }
                
            })
        });

        }, 1000);
    }
    function steemconnect(){
        ses=true
        steemc=true
        sesion();
    }
