import {$,state,api,esc,money,showDialog,toast} from "./api.js";
import {renderCategories,loadProducts,wireCatalogue} from "./catalogue.js";
import {wireChat} from "./chat.js";
import {getLanguage,setLanguage,startLocalization,localize,setLanguageBusy} from "./i18n.js";
import {wireProductPages,renderProductRoute} from "./product-page.js";

startLocalization();

function updateMode(config) {
 state.config=config;
 const model=config.mode==="model";
 $("#mode-label").textContent=model?"Model configured · "+config.model:"Catalogue preview";
 $("#preview-note").hidden=model;$("#open-settings").textContent=model?"Model settings ↗":"Connect a model ↗";
 $("#base-url").value=config.base_url;$("#model-id").value=config.model;
 $("#api-key").value="";$("#api-key").placeholder=config.has_key?"Session key saved · leave empty to keep":"API key, if required";
}
function settingsBody() {
 return {base_url:$("#base-url").value.trim(),model:$("#model-id").value.trim(),
   api_key:$("#api-key").value||null,no_key:$("#no-key").checked};
}
async function saveSettings() {const config=await api("/api/config",settingsBody());updateMode(config);return config;}
function settingsMessage(text,error=false) {$("#settings-message").textContent=text;$("#settings-message").classList.toggle("error",error);}
for(const button of ["#open-settings","#connect-inline"])$(button).addEventListener("click",()=>{settingsMessage("");showDialog("#settings-dialog");});
document.querySelectorAll(".close-dialog").forEach(b=>b.addEventListener("click",()=>b.closest("dialog").close()));
document.querySelectorAll("dialog").forEach(dialog=>dialog.addEventListener("click",event=>{
 const rect=dialog.getBoundingClientRect();if(event.target===dialog&&(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom))dialog.close();
}));
$("#provider-preset").addEventListener("change",()=>{
 const value=$("#provider-preset").value;if(value!=="custom"){$("#base-url").value=value;$("#no-key").checked=value.startsWith("http://localhost");}
});
$("#settings-form").addEventListener("submit",async event=>{
 event.preventDefault();try{await saveSettings();$("#settings-dialog").close();toast("Connection saved. Send a message to try tool calling.");}catch(error){settingsMessage(error.message,true);}
});
$("#load-models").addEventListener("click",async()=>{
 const button=$("#load-models");button.disabled=true;settingsMessage("Looking for models…");
 try{await saveSettings();const result=await api("/api/models",{});
 $("#model-options").innerHTML=result.models.map(id=>'<option value="'+esc(id)+'"></option>').join("");
 if(!$("#model-id").value&&result.models.length===1)$("#model-id").value=result.models[0];
 settingsMessage(result.models.length+" model(s) found. Choose a model from the Model ID field. Tool support is not yet verified.");}
 catch(error){settingsMessage(error.message+" You can enter the model ID manually.",true);}
 finally{button.disabled=false;}
});
$("#use-preview").addEventListener("click",async()=>{
 try{updateMode(await api("/api/config",{base_url:"",model:"",no_key:true}));$("#settings-dialog").close();toast("Catalogue preview enabled.");}
 catch(error){settingsMessage(error.message,true);}
});
$("#order-lookup").addEventListener("click",()=>showDialog("#order-dialog"));
$("#order-form").addEventListener("submit",async event=>{
 event.preventDefault();const output=$("#order-result");output.textContent="Checking the supplied snapshot…";output.classList.remove("error");
 try{const result=await api("/api/orders/verify",{order_id:Number($("#order-id").value),email:$("#order-email").value});
 const o=result.order;output.textContent="Order #"+o.order_id+" · "+o.status+"\nTotal "+money(o.total_cents)+
 (o.tracking_code?"\nTracking "+o.tracking_code:"\nNo tracking reference recorded.")+
 "\n"+result.note;$("#order-email").value="";}
 catch(error){output.textContent=error.message;output.classList.add("error");}
});
$("#open-tools").addEventListener("click",async()=>{
 try{const result=await api("/api/tools");$("#tool-list").innerHTML=result.tools.map(t=>
 '<section class="tool-doc"><h3>'+esc(t.name)+'</h3><p>'+esc(t.description)+'</p><p>'+esc(t.access)+' '+esc(t.side_effects)+'</p><details><summary>Input schema</summary><pre>'+esc(JSON.stringify(t.input_schema,null,2))+'</pre></details><details><summary>Result schema</summary><pre>'+esc(JSON.stringify(t.output_schema,null,2))+'</pre></details></section>').join("");showDialog("#tools-dialog");}
 catch(error){toast(error.message);}
});
wireCatalogue();wireChat();wireProductPages();
document.querySelectorAll("[data-language]").forEach(button=>button.addEventListener("click",async()=>{
 if(state.busy||button.dataset.language===getLanguage())return;
 state.languageBusy=true;setLanguageBusy(true);$("#send-button").disabled=true;
 try{
  const result=await api("/api/language",{language:button.dataset.language});
  state.language=result.language;setLanguage(result.language);
  renderCategories();await loadProducts();
  if(state.selected)state.selected=state.cache.get(state.selected.product_id)??state.selected;
  await renderProductRoute();
  updateMode(state.config);localize();
  toast(result.language==="pt-BR"?"Português (Brasil) ativo. As próximas respostas serão em português.":"English active. Future replies will be in English.");
 }catch(error){toast(error.message);}
 finally{state.languageBusy=false;setLanguageBusy(false);$("#send-button").disabled=state.busy;}
}));
document.addEventListener("category-state-changed",renderCategories);
document.addEventListener("collection-requested",()=>{renderCategories();loadProducts();});
try{await api("/api/language",{language:getLanguage()});const boot=await api("/api/bootstrap");state.categories=boot.categories;$("#total-count").textContent=boot.product_count;
 updateMode(boot.config);renderCategories();await loadProducts();await renderProductRoute();}
catch(error){toast(error.message);$("#result-count").textContent="Server unavailable";}
