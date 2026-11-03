import {getLanguage,text} from "./i18n.js";
export const $ = selector => document.querySelector(selector);
export const money = cents => new Intl.NumberFormat(getLanguage()==="pt-BR"?"pt-BR":"en-US", {style:"currency",currency:"BRL"}).format(cents / 100);
export const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
export const state = {language:getLanguage(),category:null,selected:null,products:[],cache:new Map(),categories:[],config:{mode:"preview"},busy:false,languageBusy:false};
export async function api(path, body, options={}) {
  if(body===undefined&&path.startsWith("/api/products"))path+=(path.includes("?")?"&":"?")+"language="+getLanguage();
  const response = await fetch(path, {credentials:"same-origin",...options,
    ...(body === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})});
  if (!response.ok) {
    let data; try {data=await response.json();} catch {data={};}
    const detail = Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join(" ") : data.detail;
    throw new Error(text(detail || "The request could not be completed. Please try again."));
  }
  return response.json();
}
let toastTimer;
export function toast(message) {
  $("#toast").textContent=message; $("#toast").hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>$("#toast").hidden=true,5000);
}
export function context() {
  return {category_id:state.category,selected_product_id:state.selected?.product_id ?? null,
    max_price:$("#max-price").value ? Number($("#max-price").value) : null,
    payment:$("#payment").value,visible_product_ids:state.products.map(p=>p.product_id)};
}
export function showDialog(id) { $(id).showModal(); }
export function announceContext() { document.dispatchEvent(new Event("catalogue-context")); }
