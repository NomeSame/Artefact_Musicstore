import {$,state,api,esc,money,context,announceContext,toast} from "./api.js";
import {selectProduct,renderCategories,loadProducts} from "./catalogue.js";
import {productQuestions} from "./product-page.js";

function renderProductQuestions(product) {
 const area=$("#product-questions");
 area.innerHTML='<h3>What would you like to know?</h3><p>Choose a starting point, then edit or send your question.</p><div class="chat-topic-buttons">'+
  productQuestions(product).map((q,i)=>'<button type="button" data-topic="'+i+'">'+esc(q.label)+'</button>').join("")+
  '</div><button type="button" class="text-button" id="chat-own-question">Write my own question ↗</button>';
 area.querySelectorAll("[data-topic]").forEach(button=>button.addEventListener("click",()=>{
  $("#chat-input").value=productQuestions(product)[Number(button.dataset.topic)].prompt;
  $("#chat-input").focus({preventScroll:true});
 }));
 $("#chat-own-question").addEventListener("click",()=>{
  $("#chat-input").value="";$("#chat-input").focus({preventScroll:true});
 });
}
function prepareProductChat({product,prompt=""}) {
 state.selected=product;state.category=product.category_id;announceContext();
 renderProductQuestions(product);$("#product-questions").hidden=false;
 $("#suggestions").hidden=true;$("#chat-input").value=prompt;
 document.querySelector(".assistant-panel").scrollIntoView({behavior:"smooth",block:"start"});
 $("#chat-input").focus({preventScroll:true});
}

function addMessage(role,text) {
 const node=document.createElement("div");node.className="message "+(role==="user"?"user-message":"assistant-message");
 const meta=document.createElement("div");meta.className="message-meta";meta.textContent=role==="user"?"YOU":"EMPÓRIO GUIDE";
 const p=document.createElement("p");p.textContent=text;node.append(meta,p);$("#messages").append(node);
 $("#messages").scrollTop=$("#messages").scrollHeight;return node;
}
export async function sendMessage(text) {
 if(state.busy||!text.trim())return;
 state.busy=true;$("#send-button").disabled=true;$("#chat-input").value="";
 $("#suggestions").hidden=true;addMessage("user",text);
 const pending=addMessage("assistant","Looking into that…");pending.classList.add("thinking");
 try{
   const result=await api("/api/chat",{message:text,context:context()});
   pending.remove();const node=addMessage("assistant",result.answer);
   for(const p of result.products) {
    state.cache.set(p.product_id,p);
    const b=document.createElement("button");b.className="chat-product";
    b.innerHTML="<strong>"+esc(p.name)+"</strong><span>"+money(p.price_cents)+(p.available?" · Available":" · Unavailable")+"</span>";
    b.addEventListener("click",()=>selectProduct(p.product_id));node.append(b);
   }
   for(const source of result.sources) {
    const chip=document.createElement("a");chip.className="source-chip";chip.textContent="Store manual · p. "+source.page;chip.href="/api/manual#page="+source.page;chip.target="_blank";chip.rel="noopener";node.append(chip);
   }
   if(result.trace.length) {
    const details=document.createElement("details");details.className="tool-trace";
    const summary=document.createElement("summary");summary.textContent="Consulted "+result.trace.map(t=>t.name).join(", ");
    const pre=document.createElement("pre");pre.textContent=JSON.stringify(result.trace.map(t=>({tool:t.name,arguments:t.arguments,cached:Boolean(t.cached),error:t.result.error??null})),null,2);
    details.append(summary,pre);node.append(details);
   }
   for(const action of result.actions) {
    state.category=action.category_id;state.selected=null;
    $("#search").value="";$("#max-price").value="";
    renderCategories();await loadProducts();
    if(action.product_id)selectProduct(action.product_id,false);
    announceContext();
   }
   $("#messages").scrollTop=$("#messages").scrollHeight;
 }catch(error){pending.remove();addMessage("assistant",error.message).classList.add("error-message");}
 finally{state.busy=false;$("#send-button").disabled=false;$("#chat-input").focus();}
}
export function wireChat() {
 $("#chat-form").addEventListener("submit",event=>{event.preventDefault();sendMessage($("#chat-input").value);});
 $("#chat-input").addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();sendMessage($("#chat-input").value);}});
 document.querySelectorAll("[data-prompt]").forEach(b=>b.addEventListener("click",()=>sendMessage(b.dataset.prompt)));
 document.addEventListener("prepare-product-chat",event=>prepareProductChat(event.detail));
 $("#chat-menu").addEventListener("click",()=>{const open=$("#chat-actions").hidden;$("#chat-actions").hidden=!open;$("#chat-menu").setAttribute("aria-expanded",String(open));});
 $("#reset-chat").addEventListener("click",async()=>{
  if(state.busy)return;
  try{await api("/api/chat/reset",{});$("#messages").innerHTML="";addMessage("assistant","A fresh start. What would you like to explore?");$("#chat-actions").hidden=true;}
  catch(error){toast(error.message);}
 });
 $("#export-chat").addEventListener("click",()=>{const link=document.createElement("a");link.href="/api/chat/export";link.download="conversation.md";link.click();});
 $("#clear-selection").addEventListener("click",()=>{state.selected=null;announceContext();});
 document.addEventListener("catalogue-context",()=>{
  const category=state.categories.find(c=>c.category_id===state.category)?.label??"All instruments";
  $("#context-label").textContent=category;$("#selected-context").hidden=!state.selected;
  $("#selected-name").textContent=state.selected?.name??"";
  if(!state.selected)$("#product-questions").hidden=true;
  else if(!$("#product-questions").hidden)renderProductQuestions(state.selected);
 });
}
