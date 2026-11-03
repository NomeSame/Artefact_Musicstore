import {$,state,api,esc,money,announceContext,toast} from "./api.js";
import {instrument} from "./art.js";

const LABELS={top:"Top",back_sides:"Back & sides",neck:"Neck",strings:"Strings",scale:"Scale length",
 electronics:"Electronics",color:"Colour",body:"Body",pickups:"Pickups",pickup:"Pickup",
 keys:"Keys",type:"Type",polyphony:"Polyphony",size:"Size",fingerboard:"Fingerboard",frets:"Frets"};
export function productQuestions(product) {
 const isKeys=product?.category_id===4;
 return [
  {label:"Build & materials",prompt:"What are the materials and technical specifications of this instrument?"},
  {label:isKeys?"Keys & sound options":"Sound & electronics",prompt:"What sound-related specifications and electronics are recorded for this instrument?"},
  {label:"Stock & availability",prompt:"Is this instrument available, and how many are in stock?"},
  {label:"Price & payment",prompt:"What does this instrument cost with PIX?"},
  {label:"Delivery",prompt:"What are the delivery options and rules for this instrument?"},
  {label:"Returns",prompt:"What are the return conditions for this instrument?"},
  {label:"Warranty",prompt:"What warranty information is available for this instrument?"},
 ];
}
export function askAboutProduct(product,prompt="") {
 state.selected=product;state.category=product.category_id;announceContext();
 document.dispatchEvent(new CustomEvent("prepare-product-chat",{detail:{product,prompt}}));
}
let routeVersion=0;
export async function renderProductRoute() {
 const version=++routeVersion;
 const match=location.pathname.match(/^\/products\/(\d+)\/?$/);
 const page=$("#product-page");
 $("#catalogue-view").hidden=Boolean(match);
 page.hidden=!match;
 if(!match){document.title="Empório da Música · Find your next sound";return;}
 page.innerHTML='<p class="route-loading">Finding your instrument…</p>';
 try {
  const data=await api("/api/products/"+match[1]+"?payment="+encodeURIComponent($("#payment").value));
  if(version!==routeVersion)return;
  const p=data.product;
  state.cache.set(p.product_id,p);state.selected=p;state.category=p.category_id;announceContext();
  document.dispatchEvent(new Event("category-state-changed"));
  document.title=p.name+" · Empório da Música";
  const facts=Object.entries(p.specs);
  const primary=facts.slice(0,4);
  const missing=[["weight","Weight"],["included_accessories","Included case and accessories"],
   ["handedness","Handedness"],["manufacturer_warranty","Model-specific manufacturer warranty"]].filter(([key])=>!(key in p.specs));
  page.innerHTML=
   '<nav class="product-breadcrumb" aria-label="Breadcrumb"><a href="/" data-catalogue-link>Collection</a><span>/</span><span>'+esc(p.category_label)+'</span><span>/</span><span>'+esc(p.name)+'</span></nav>'+
   '<a href="/" class="back-to-collection" data-catalogue-link>← Back to the collection</a>'+
   '<div class="product-page-hero"><div class="product-page-art">'+instrument(p.category_id,p.product_id)+
   '<span class="illustration-caption">Instrument illustration</span></div><div class="product-page-heading">'+
   '<div class="eyebrow">'+esc(p.category_label)+'</div><h1>'+esc(p.name)+'</h1>'+
   '<p class="product-stock '+(p.available?"":"not-available")+'"><span class="status-dot"></span>'+
   (p.available?p.stock_quantity+' available':esc(p.status==="active"?"Out of stock":p.status.replaceAll("_"," ")))+'</p>'+
   '<div class="page-price"><strong>'+money(p.price_cents)+'</strong>'+
   (p.discount_percent?'<del>'+money(p.list_cents)+'</del><span class="discount-pill">'+p.discount_percent+'% off</span>':'')+'</div>'+
   '<p class="price-condition">'+(p.payment==="pix"?'Price with full PIX payment.':'Current quote. Best price with full PIX payment '+money(p.pix_price_cents)+'.')+' Discounts never stack.</p>'+
   '<div class="product-highlights">'+primary.map(([key,value])=>'<div><span>'+esc(LABELS[key]??key.replaceAll("_"," "))+'</span><strong>'+esc(value)+'</strong></div>').join("")+'</div>'+
   '<button class="primary-button" id="page-ask-product">Talk to your music guide ↗</button>'+
   '<p class="page-ask-note">Explore the details, choose a question or write your own. Nothing is sent until you press Send.</p>'+
   '</div></div>'+
   '<nav class="product-section-links" aria-label="Product information"><a href="#product-overview">Overview</a><a href="#product-specs">Specifications</a><a href="#product-buying">Before you choose</a><a href="#product-store-policies">Delivery & care</a></nav>'+
   '<section class="product-page-section" id="product-overview"><span class="eyebrow">GET TO KNOW THE INSTRUMENT</span><h2>A closer look.</h2>'+
   '<p class="product-description" lang="pt-BR">'+esc(p.description)+'</p><p class="source-caption">Original catalogue description. Ask the guide to explore the recorded specifications.</p></section>'+
   '<section class="product-page-section" id="product-specs"><div class="section-title-row"><div><span class="eyebrow">THE DETAILS THAT MATTER</span><h2>Specifications.</h2></div><button class="text-button" data-question="0">Discuss the specifications ↗</button></div>'+
   '<dl class="full-specs">'+facts.map(([key,value])=>'<div><dt>'+esc(LABELS[key]??key.replaceAll("_"," "))+'</dt><dd>'+esc(value)+'</dd></div>').join("")+'</dl></section>'+
   '<section class="product-page-section" id="product-buying"><span class="eyebrow">FIND YOUR FIT</span><h2>Before you choose.</h2>'+
   '<p>How an instrument feels in your hands matters as much as the specifications. Tell the guide about your experience, the music you play and where you plan to use it.</p>'+
   (missing.length?'<div class="confirm-details"><h3>Worth confirming with the team</h3><p>'+missing.map(([,label])=>esc(label)).join(", ")+'. These details are not recorded for this instrument.</p></div>':'')+
   '<div class="product-question-grid">'+productQuestions(p).map((q,i)=>'<button data-question="'+i+'"><span>'+esc(q.label)+'</span><span aria-hidden="true">↗</span></button>').join("")+'</div>'+
   '<button class="secondary-button own-question" id="page-own-question">Something else? Write your own question ↗</button></section>'+
   '<section class="product-page-section" id="product-store-policies"><span class="eyebrow">A LITTLE PEACE OF MIND</span><h2>Delivery, returns & care.</h2>'+
   '<div class="product-policy-grid">'+data.policies.map(policy=>'<article><h3>'+esc(policy.topic==="returns"?"Returns":policy.topic==="warranty"?"Warranty":"Delivery")+'</h3><p>'+esc(policy.summary)+'</p>'+
   policy.sources.map(source=>'<a class="source-chip" target="_blank" rel="noopener" href="/api/manual#page='+source.page+'">Store manual · p. '+source.page+'</a>').join("")+'</article>').join("")+'</div></section>'+
   '<p class="product-page-footnote">Availability and prices come from the supplied store catalogue. This prototype does not take payments or place orders.</p>';
  page.querySelectorAll("[data-catalogue-link]").forEach(link=>link.addEventListener("click",event=>{event.preventDefault();showCollection();}));
  page.querySelectorAll("[data-question]").forEach(button=>button.addEventListener("click",()=>askAboutProduct(p,productQuestions(p)[Number(button.dataset.question)].prompt)));
  $("#page-ask-product").addEventListener("click",()=>askAboutProduct(p));
  $("#page-own-question").addEventListener("click",()=>askAboutProduct(p));
 }catch(error) {
  if(version!==routeVersion)return;
  page.innerHTML='<div class="empty-state"><h1>We could not find that instrument.</h1><p>'+esc(error.message)+'</p><a class="primary-button" href="/">Back to the collection</a></div>';
 }
}
export async function openProductPage(id) {
 const path="/products/"+id;
 if(location.pathname!==path)history.pushState({product:id},"",path);
 await renderProductRoute();window.scrollTo({top:0,behavior:"smooth"});
}
export function showCollection() {
 if(location.pathname!=="/")history.pushState({},"","/");
 renderProductRoute();document.dispatchEvent(new Event("collection-requested"));
}
export function wireProductPages() {
 window.addEventListener("popstate",async()=>{
  await renderProductRoute();
  if(location.pathname==="/")document.dispatchEvent(new Event("collection-requested"));
 });
 document.addEventListener("open-product-page",event=>openProductPage(event.detail));
 document.addEventListener("show-collection",showCollection);
}
