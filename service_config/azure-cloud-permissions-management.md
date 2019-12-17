---
layout: default
---

# azure微软云之权限的管理

微软云对主机资源是分割开来的，即cpu、内存、内网、外网、磁盘、网络安全组都是可以拆开、合并的资源。这样导致的结果是所有的资源都可以单独给予权限。以下以powershell操作

登录

```
Login-AzureRmAccount -EnvironmentName AzureChinaCloud
```

选择订阅id

```
Set-AzureRmContext -SubscriptionId ****-**-**-**-****
```

订阅名称,订阅ID在自己账户即可查看

创建ad的用户名密码

```
$azureAdApplication = New-AzureRmADApplication -DisplayName "bbotte" -HomePage "http://bbotte.com" -IdentifierUris "http://bbotte.com" -Password "123456"
```

查看当前设置的信息

```
$azureAdApplication
```

创建服务凭证

```
New-AzureRmADServicePrincipal -ApplicationId $azureAdApplication.ApplicationId
```

添加角色设置，添加Reader只读授权

```
New-AzureRmRoleAssignment -RoleDefinitionName Reader -ServicePrincipalName $azureAdApplication.ApplicationId
```

验证权限

```
Get-AzureRMRoleDefinition -Name "Reader"
```

以上几步即完成某订阅下只读权限的添加，下面是有关命令的操作：

```
查看本人有哪些权限
Get-AzureRMResourceProvider
通过权限名称获取权限信息
Get-AzureRMRoleDefinition -Name "bbotte-service-bus02"
列出角色的操作
(Get-AzureRmRoleDefinition bbotte-service-bus02).Actions
把权限另存为json文件
Get-AzureRMRoleDefinition -Name "Reader" | ConvertTo-Json | Out-File e:\rbacrole2.json
通过json文件新增一个权限
New-AzureRmRoleDefinition -InputFile "e:\rbacrole2.json"
通过json文件更新权限
Set-AzureRmRoleDefinition -InputFile "e:\rbacrole2.json"
查看资源组谁具有访问权限
Get-AzureRmRoleAssignment -ResourceGroupName dev-service
查看以"bbotte"命名开头的应用权限
Get-AzureRmADApplication -DisplayNameStartWith "bbotte"
查看包含"bbotte"命名的应用权限
Get-AzureRmADApplication -DisplayName "bbotte"
删除一个应用权限，一般不用-Force，如果不加-Force不能删除，说明此权限有其他应用在使用
Remove-AzureRmADApplication -ObjectId objectid_number -Force
查看权限规则信息
Get-AzureRmRoleDefinition |FT Name, Id, IsCustom|findstr matuoyi
按id删除权限规则
Remove-AzureRmRoleDefinition -Id id_number
按名称删除权限规则
Get-AzureRmRoleDefinition "Virtual Machine Operator" | Remove-AzureRmRoleDefinition
```

例子：

分配某订阅下dev组服务总线的权限

```
New-AzureRmRoleDefinition -InputFile "e:\rbacrole2.json"
e:\rbacrole2.json文件内容如下：
 
{
    "Name":  "bbotte-service-bus02",
    "Id":  "*****-****-****-****-****",
    "IsCustom":  false,
    "Description":  "just for Service Bus.",
    "Actions":  [
                    "Microsoft.ServiceBus/*"
                ],
    "NotActions":  [
 
                   ],
    "AssignableScopes":  [
                             "/subscriptions/*****-****-****-****-****/resourceGroups/dev-service"
                         ]
}
```

Actions是选择赋予权限的服务

AssignableScopes可以精确到一个资源组或一个资源

NotActions是对Actions的附加，比如Actions有设置dev组服务总线下所有的权限，如上json，那么可以在NotActions添加禁止对某一个服务总线访问，NotActions是对Actions的补充
创建用户名密码：

```
$azureAdApplication = New-AzureRmADApplication -DisplayName "zhangsan_servicebus" -HomePage "http://zhangsan_servicebus.com" -IdentifierUris "http://zhangsan_servicebus.com" -Password "123456"
```

查看创建的信息

```
$azureAdApplication
```

下面几步可以通过web界面操作

创建服务凭证

```
New-AzureRmADServicePrincipal -ApplicationId $azureAdApplication.ApplicationId
```

把新建权限附加给用户

如果角色是针对订阅的则：

```
New-AzureRmRoleAssignment -RoleDefinitionName "bbotte-service-bus02" -ServicePrincipalName $azureAdApplication.ApplicationId
```

如果角色是针对资源组的则：

```
New-AzureRmRoleAssignment -RoleDefinitionName "bbotte-service-bus02" -ServicePrincipalName $azureAdApplication.ApplicationId -Scope "/subscriptions/****-****-****-****-****/resourceGroups/test-service"
```

把以下信息发送给开发，api需要的信息：

```
ApplicationId : ****-****-****-****-****
TENANTID : ****-****-****-****-****(Directory ID，也叫做Tenant ID或者租户ID通过portal管理界面’AD’-‘属性’获取)
resourceGroup : dev-service
订阅ID : ****-****-****-****-****
appSecret : 123456
```

2018年03月03日 于 [linux工匠](http://www.bbotte.com/) 发表