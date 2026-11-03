import {$,state,api,esc,money,context,announceContext,toast} from "./api.js";
import {selectProduct,renderCategories,loadProducts} from "./catalogue.js";
import {getLanguage,text as localText,setLanguageBusy} from "./i18n.js";
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
 if($("#suggestions"))$("#suggestions").hidden=true;$("#chat-input").value=prompt;
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
 if(state.busy||state.languageBusy||!text.trim())return;
 document.querySelectorAll(".navigation-proposal").forEach(button=>button.disabled=true);
 state.busy=true;setLanguageBusy(true);$("#send-button").disabled=true;$("#chat-input").value="";
 if($("#suggestions"))$("#suggestions").hidden=true;addMessage("user",text);
 const pending=addMessage("assistant",localText("Looking into that…"));pending.classList.add("thinking");
 try{
   const result=await api("/api/chat",{message:text,context:context(),language:getLanguage()});
   pending.remove();const node=addMessage("assistant",result.answer);node.lang=result.language??getLanguage();
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
   // Model-suggested navigation is never applied automatically.
   for(const proposal of result.navigation_proposals??[]) {
    const button=document.createElement("button");button.type="button";button.className="chat-product navigation-proposal";
    button.textContent="Open "+proposal.label;
    button.addEventListener("click",async()=>{
     if(state.busy)return;
     button.disabled=true;
     try{
      const {action}=await api("/api/navigation/confirm",{proposal_id:proposal.id});
      state.category=action.category_id;state.selected=null;
      $("#search").value="";$("#max-price").value="";
      renderCategories();await loadProducts();
      if(action.product_id)await selectProduct(action.product_id,false);
      announceContext();button.textContent="Opened "+proposal.label;
     }catch(error){toast(error.message);button.textContent="Suggestion no longer available";}
    });
    node.append(button);
   }
   $("#messages").scrollTop=$("#messages").scrollHeight;
 }catch(error){pending.remove();addMessage("assistant",error.message).classList.add("error-message");}
 finally{state.busy=false;setLanguageBusy(false);$("#send-button").disabled=false;$("#chat-input").focus();}
}
export function wireChat() {
 document.addEventListener("language-changed",()=>{
  document.querySelectorAll(".navigation-proposal").forEach(button=>{button.disabled=true;button.textContent=localText("Suggestion no longer available");});
  if(state.selected&&!$("#product-questions").hidden)renderProductQuestions(state.selected);
 });
 $("#chat-form").addEventListener("submit",event=>{event.preventDefault();sendMessage($("#chat-input").value);});
 $("#chat-input").addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();sendMessage($("#chat-input").value);}});
 document.querySelectorAll("[data-prompt]").forEach(b=>b.addEventListener("click",()=>sendMessage(localText(b.dataset.prompt))));
 document.addEventListener("prepare-product-chat",event=>prepareProductChat(event.detail));
 $("#chat-menu").addEventListener("click",()=>{const open=$("#chat-actions").hidden;$("#chat-actions").hidden=!open;$("#chat-menu").setAttribute("aria-expanded",String(open));});
 $("#reset-chat").addEventListener("click",async()=>{
  if(state.busy)return;
  try{await api("/api/chat/reset",{});$("#messages").querySelectorAll(".message").forEach(message=>message.remove());
   document.querySelectorAll(".navigation-proposal").forEach(button=>button.remove());
   addMessage("assistant",localText("A fresh start. What would you like to explore?"));$("#chat-actions").hidden=true;}
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
