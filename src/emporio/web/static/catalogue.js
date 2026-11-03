import {$,state,api,esc,money,announceContext,showDialog,toast} from "./api.js";
import {instrument} from "./art.js";
let requestId=0;
export function renderCategories() {
 $("#categories").innerHTML=[{category_id:null,label:"All instruments",count:$("#total-count").textContent},...state.categories].map(c=>
  '<button class="category-button'+(state.category===c.category_id?' active':'')+'" data-category="'+(c.category_id??"")+'"><span class="category-icon" aria-hidden="true">'+(c.category_id??"∿")+'</span><span>'+esc(c.label)+'</span><span class="category-count">'+c.count+'</span></button>').join("");
 $("#categories").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>{
   document.dispatchEvent(new Event("show-collection"));
   state.category=button.dataset.category?Number(button.dataset.category):null; state.selected=null;
   $("#search").value="";renderCategories();loadProducts();announceContext();
 }));
}
export async function loadProducts() {
 const id=++requestId;
 const params=new URLSearchParams({query:$("#search").value,payment:$("#payment").value,sort:$("#sort").value,
   available_only:$("#available-only").checked});
 if(state.category)params.set("category_id",state.category);
 if($("#max-price").value)params.set("max_price",$("#max-price").value);
 $("#result-count").textContent="Updating collection…";
 try{
  const result=await api("/api/products?"+params);
  if(id!==requestId)return;
  state.products=result.products;
  for(const p of state.products)state.cache.set(p.product_id,p);
  $("#catalogue-title").textContent=state.categories.find(c=>c.category_id===state.category)?.label??"All instruments";
  $("#result-count").textContent=result.count+" instrument"+(result.count===1?"":"s");
  $("#empty").hidden=result.count>0;renderProducts();announceContext();
 }catch(error){if(id===requestId){$("#result-count").textContent="Could not load instruments";toast(error.message);}}
}
function badge(p) {
 if(!p.available)return '<span class="product-badge unavailable">'+esc(p.status==="active"?"OUT OF STOCK":p.status.replaceAll("_"," ").toUpperCase())+'</span>';
 if(p.discount_percent)return '<span class="product-badge sale">−'+p.discount_percent+'%</span>';
 return '<span class="product-badge">IN STOCK</span>';
}
export function renderProducts() {
 $("#products").innerHTML=state.products.map(p=>'<article class="product-card'+(state.selected?.product_id===p.product_id?' selected':'')+'">'+badge(p)+
  '<button class="product-art" data-product="'+p.product_id+'" aria-label="View '+esc(p.name)+'">'+instrument(p.category_id,p.product_id)+'</button>'+
  '<div class="product-body"><div class="product-category">'+esc(p.category_label)+'</div><h3 class="product-name">'+esc(p.name)+'</h3>'+
  '<div class="price-row"><span class="price">'+money(p.price_cents)+'</span>'+(p.discount_percent?'<span class="original-price">'+money(p.list_cents)+'</span>':'')+'</div>'+
  '<div class="stock"><span>'+(p.available?'<span class="status-dot"></span>'+p.stock_quantity+' available':'Currently unavailable')+'</span><button class="card-detail-button" data-product="'+p.product_id+'">Explore ↗</button></div></div></article>').join("");
 $("#products").querySelectorAll("[data-product]").forEach(b=>b.addEventListener("click",()=>selectProduct(Number(b.dataset.product))));
}
export async function selectProduct(id,open=true) {
 const p=state.cache.get(id);if(!p){toast("This instrument is not in the current catalogue.");return;}
 state.selected=p;
 if(state.category!==p.category_id){state.category=p.category_id;$("#search").value="";$("#max-price").value="";renderCategories();await loadProducts();}
 renderProducts();announceContext();
 if(!open)return;
 $("#product-detail").innerHTML='<div class="detail-layout"><div class="detail-art">'+instrument(p.category_id,p.product_id)+'</div><div class="detail-content"><span class="eyebrow">'+esc(p.category_label)+'</span><h2>'+esc(p.name)+'</h2><div class="price-row"><span class="price">'+money(p.price_cents)+'</span>'+(p.discount_percent?'<span class="original-price">'+money(p.list_cents)+'</span>':'')+'</div><p>'+esc(p.description)+'</p><p>'+(p.available?p.stock_quantity+' available':'Currently unavailable')+' · Snapshot data</p><dl>'+Object.entries(p.specs).map(([key,value])=>'<dt>'+esc(key.replaceAll("_"," "))+'</dt><dd>'+esc(value)+'</dd>').join("")+'</dl><p>Best PIX price '+money(p.pix_price_cents)+'. Full immediate payment to the store, no combined discounts.</p><a class="primary-button product-page-link" href="/products/'+p.product_id+'" id="view-product-page">View full product page ↗</a><button class="secondary-button" id="ask-product">Ask about this instrument ↗</button></div></div>';
 showDialog("#product-dialog");
 $("#ask-product").addEventListener("click",()=>{$("#product-dialog").close();document.dispatchEvent(new CustomEvent("prepare-product-chat",{detail:{product:p,prompt:""}}));});
 $("#view-product-page").addEventListener("click",event=>{event.preventDefault();$("#product-dialog").close();document.dispatchEvent(new CustomEvent("open-product-page",{detail:p.product_id}));});
}
export function resetFilters() {
 state.category=null;state.selected=null;
 $("#search").value="";$("#max-price").value="";$("#payment").value="unspecified";$("#available-only").checked=false;$("#sort").value="recommended";
 renderCategories();loadProducts();announceContext();
}
export function wireCatalogue() {
 let debounce;$("#search").addEventListener("input",()=>{clearTimeout(debounce);debounce=setTimeout(loadProducts,200);});
 for(const id of ["#sort","#max-price","#payment","#available-only"])$(id).addEventListener("change",loadProducts);
 $("#toggle-filters").addEventListener("click",()=>{const open=$("#extra-filters").hidden;$("#extra-filters").hidden=!open;$("#toggle-filters").setAttribute("aria-expanded",String(open));});
 $("#reset-filters").addEventListener("click",resetFilters);$("#clear-search").addEventListener("click",resetFilters);
}
