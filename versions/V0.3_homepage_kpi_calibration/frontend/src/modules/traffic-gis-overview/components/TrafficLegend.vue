<template>
  <div class="legend">
    <span><i class="route"></i>高速主线</span
    ><span><i class="normal"></i>正常</span
    ><span><i class="attention"></i>关注</span
    ><span><i class="warning"></i>风险</span
    ><span><i class="zone"></i>范围</span>
  </div>
</template>
<style scoped>
.legend {
  display: flex;
  gap: 14px;
  padding: 7px 11px;
  background: rgba(4, 24, 48, 0.8);
  border: 1px solid rgba(34, 135, 255, 0.4);
  font-size: 11px;
  color: #a9c9da;
}
.legend span {
  display: flex;
  align-items: center;
  gap: 5px;
}
.legend i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.route {
  background: #22d7ff;
}
.normal {
  background: #39e27d;
}
.attention {
  background: #f5c542;
}
.warning {
  background: #ff4d5a;
}
.zone {
  background: #9a6cff;
}
</style>
