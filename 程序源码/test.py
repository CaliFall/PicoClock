dic = {"a":123,
       "b":"hello",
       "c":"wtf"}
a = list(dic.items())
for i in range(len(a)):
       a[i] = list(a[i])
print(a)