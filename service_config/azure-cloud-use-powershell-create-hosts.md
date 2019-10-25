# azure微软云之powershell创建主机

利用powershell创建主机，需要先做一个模板，下面是ARM模式下的过程，另外需注意azure是以资源组隔离的，即模板所在的资源组不能被其他资源组利用，如果有多个资源组，需要创建多个模板

ARM模式下只能**制作一般化（Generalized）的映像**

Windows主机使用Sysprep进行一般化操作，Linux虚拟机使用waagent -deprovision命令进行一般化操作，完成后在后台portal界面点击“停止”主机，主机状态会变为“已停止(已取消分配)”，具体操作如下：

一、开通一个azure主机，完成系统配置后，执行waagent -deprovision

```
# waagent -deprovision
WARNING! The waagent service will be stopped.
WARNING! All SSH host key pairs will be deleted.
WARNING! Cached DHCP leases will be deleted.
WARNING! root password will be disabled. You will not be able to login as root.
WARNING! /etc/resolv.conf will be deleted.
Do you want to proceed (y/n)y
2017/09/27 18:11:56.067417 INFO Examine /proc/net/route for primary interface
2017/09/27 18:11:56.075867 INFO Primary interface is [eth0]
2017/09/27 18:11:56.091003 INFO interface [lo] has flags [73], is loopback [True]
2017/09/27 18:11:56.099541 INFO Interface [lo] skipped
2017/09/27 18:11:56.111943 INFO interface [eth0] has flags [4163], is loopback [False]
2017/09/27 18:11:56.149599 INFO Interface [eth0] selected
```

二，关闭此主机

三，Generalized操作

使用Azure Powershell将已经做完Sysprep或者waagent -deprovision的主机标记为Generalized的虚拟机（这里省略了Login和设置订阅的过程）：

```
Set-AzureRmVM -ResourceGroupName <Resource Group Name> -Name <VM Name> -Generalized
```

设置完成后，保存映像：

```
Save-AzureRmVMImage -ResourceGroupName <Resource Group Name> -VMName <VM Name> -DestinationContainerName <Container Name> -VHDNamePrefix <Custom VHD Name Prefix>
```

```
PowerShell：
Login-AzureRmAccount -EnvironmentName AzureChinaCloud
Set-AzureRmVM -ResourceGroupName test-service -Name bbotte -Generalized
Save-AzureRmVMImage -ResourceGroupName test-service -VMName bbotte -DestinationContainerName centos7template -VHDNamePrefix centos7template
```

注意：DestinationContainerName的名称需要由3-63个小写或连字符组成，不能有大写字母。与经典模式的一般化映像有一点区别，ARM模式下捕获完成后，原虚拟机不会自动删除。

保存映像操作完成后，我们找到虚拟机所在的存储账号下，发现下面多了一个名为system的container

获取镜像的链接,在此主机存储账户下

```
Location:system/Microsoft.Compute/Images/centos7template
```

![]()

在system下面依次找到Microsoft.Compute->Images->danimagecontainer（我们前面创建的container的名字），在里面可以找到我们捕获的映像对应的vhd文件，我们就可以用此vhd文件来创建主机。

五、删除此主机资源、vhd、网络信息等

tips：
因为powershell用镜像创建主机后，登录密码失败，所以用公钥

```
/opt/add_key.sh
#!/bin/bash
if [ ! -d /root/.ssh ];then
mkdir /root/.ssh
chmod 700 /root/.ssh
fi
auth_key=`grep zabbix /root/.ssh/authorized_keys` 
echo $auth_key
if [ ! -n "$auth_key" ];then
echo 'ssh-rsa AAAAB3Nz************VBdXCYP3U= zabbix' >> /root/.ssh/authorized_keys
fi
 
chmod +x /opt/add_key.sh
chmod +x /etc/rc.d/rc.local
/etc/rc.local
sh /opt/add_key.sh
```

**power shell创建主机**

以已保存的磁盘文件作为镜像/模板创建主机

```
powershell 4.3.1
http://aka.ms/webpi-azps
```

登录

```
Login-AzureRmAccount -EnvironmentName AzureChinaCloud
```

power shell的帮助信息：

```
帮助信息：
若要查看示例，请键入: "get-help Get-AzureRmResource -examples".
有关详细信息，请键入: "get-help Get-AzureRmResource -detailed".
若要获取技术信息，请键入: "get-help Get-AzureRmResource -full".
get-azurermresource -?
```

设置用户名密码，区域，组等

```
$username = "user";
$passwd = ConvertTo-SecureString "~!@#$%^&*()" -AsPlainText -Force;
$cred = New-Object System.Management.Automation.PSCredential($username, $passwd);
$location = "China East";
$resourceGroup = "test-service";
$storageAccount = "test";
$sourceImageUri = "https://testdisks.blob.core.chinacloudapi.cn/system/Microsoft.Compute/Images/centos7template/centos7template-osDisk.b342349.vhd";
$vmNameBase = "bbotte";
$vmSize = "Standard_DS1_v2";
$osCreatenOption = "FromImage";
$osDiskCaching = "ReadWrite";
```

指定虚拟网络和子网（已存在）

```
$virtualNetworkName = "Production-vnet";
$subnetName = "test-subnet";
$vnet = Get-AzureRmVirtualNetwork -Name $virtualNetworkName -ResourceGroupName $resourceGroup;
$subnet = Get-AzureRmVirtualNetworkSubnetConfig -Name $subnetName -VirtualNetwork $vnet;
```

创建网络安全组规则

```
$nsgRuleSSH = New-AzureRmNetworkSecurityRuleConfig -Name test-bbotte -Protocol Tcp `
-Direction Inbound -Priority 1000 -SourceAddressPrefix * -SourcePortRange * -DestinationAddressPrefix * `
-DestinationPortRange 22 -Access Allow
```

创建网络安全组

```
$nsg = New-AzureRmNetworkSecurityGroup -ResourceGroupName $resourceGroup -Location $location -Name test-bbotte -SecurityRules $nsgRuleSSH
```

批量创建主机：

```
for ($i = 1; $i -lt 1; $i += 1)
{
    #主机及磁盘名称
    $vmName = "{0}{1}" -f $vmNameBase, $i;
    $osDiskName = "{0}Disk" -f $vmName;
    $osDiskUri = "https://{0}.blob.core.chinacloudapi.cn/vhds/{1}.vhd" -f $storageAccount, $vmName
 
    # 指定IP对应的dns名称（可选）
    # $dnsNameLabelBase = "<DNS Name>";
 
    #用已创建的网络安全组
    $nsg = Get-AzureRmNetworkSecurityGroup -Name test-bbotte -ResourceGroupName $resourceGroup
 
    # 创建public IP
    $publicIPName = "{0}publicip" -f $vmName;
    # $dnsLabel = "{0}{1}" -f $vmName, $dnsNameLabelBase
    $publicIP = New-AzureRmPublicIpAddress -Name $publicIPName -ResourceGroupName `
    $resourceGroup -Location $location -AllocationMethod Dynamic; #-DomainNameLabel $dnsLabel;
    #静态公网ip
    #$publicIP = New-AzureRmPublicIpAddress -Name $publicIPName -ResourceGroupName `
    $resourceGroup -Location $location -AllocationMethod Static -IpAddressVersion IPv4 –Force
    #用已创建的公网ip
    $publicIP = Get-AzureRmPublicIpAddress -Name test-bbotte-compute01-ip -ResourceGroupName test-service
 
    # 创建NIC
    $nicName = "{0}nic" -f $vmName;
    $NIC = New-AzureRmNetworkInterface -Name $nicName -ResourceGroupName $resourceGroup `
    -Location $location -SubnetId $subnet.Id -PublicIpAddressId $publicIP.Id `
    -NetworkSecurityGroupId $nsg.Id;
    #静态内网ip
    #$NIC = New-AzureRmNetworkInterface -Name $nicName -ResourceGroupName $resourceGroup `
    -Location $location -SubnetId $subnet.Id -PublicIpAddressId `
    $publicIP.Id -NetworkSecurityGroupId $nsg.Id -PrivateIpAddress 10.0.0.6
    #用已创建的公网ip
    $NIC = New-AzureRmNetworkInterface -Name test-bbotte-compute01  -ResourceGroupName $resourceGroup -Location $location -SubnetId $subnet.Id -PublicIpAddressId $publicIP.Id -NetworkSecurityGroupId $nsg.Id #-PrivateIpAddress 10.4.0.13
 
    #组合主机信息
    $vmconfig = New-AzureRmVMConfig -VMName $vmName -VMSize $vmSize;
    Set-AzureRmVMOperatingSystem -VM $vmConfig -Linux -ComputerName $vmName -Credential $cred;
    Set-AzureRmVMOSDisk -VM $vmConfig –Name $osDiskName -VhdUri $osDiskUri -SourceImageUri `
    $sourceImageUri -Caching $osDiskCaching -CreateOption $osCreatenOption -Linux;
    Add-AzureRmVMNetworkInterface -VM $vmConfig -Id $NIC.Id -Primary;
 
    #创建主机
    New-AzureRmVM -ResourceGroupName $resourceGroup -Location $location -VM $vmConfig;
}
```

如果有提示接口出错，那么升级powershell，有遇到powershell新版本不兼容老版本

2018年03月02日 于 [linux工匠](http://www.bbotte.com/) 发表







